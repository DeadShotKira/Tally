from __future__ import annotations

import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from uuid import uuid4

from cryptography.fernet import Fernet

from backend.app.features.imports.bank_detector import BankDetector
from backend.app.features.imports.file_manager import TemporaryStatementFileManager
from backend.app.features.imports.merchant_resolver import MerchantResolver
from backend.app.features.imports.models import ImportRequest, ImportStatus, PrivacyMode
from backend.app.features.imports.parsers import StatementParserFactory
from backend.app.features.imports.privacy import PrivacyEngine
from backend.app.features.imports.repository import InMemoryImportRepository, SQLiteImportRepository
from backend.app.features.imports.service import build_default_import_service


HDFC_CSV = """Date,Narration,Chq/Ref No,Withdrawal Amt,Deposit Amt,Closing Balance
01/06/2026,UPI-METRO MART-athar@upi-9876543210,HDF001,250.50,,10000.00
02/06/2026,NEFT SALARY FROM ACME PRIVATE LTD,, ,50000.00,60000.00
03/06/2026,Account No 123456789012 IFSC HDFC0001234 Branch MG Road,HDF003,1000.00,,59000.00
bad-date,BROKEN ROW,HDF004,abc,,59000.00
"""


GENERIC_CSV = """Date,Description,Amount,Type,Balance,Reference
2026-06-01,POS Grocery Store,-1200.00,debit,8800.00,R1
2026-06-02,Salary,50000.00,credit,58800.00,R2
"""


class ImportEngineTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.temp_root = self.root / "temp"
        self.archive_root = self.root / "archive"
        self.repository = InMemoryImportRepository()
        self.file_manager = TemporaryStatementFileManager(
            temp_root=self.temp_root,
            archive_root=self.archive_root,
            archive_key=Fernet.generate_key(),
        )
        self.service = build_default_import_service(self.repository, self.file_manager)
        self.user_id = uuid4()

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _write_csv(self, name: str, content: str) -> Path:
        path = self.root / name
        path.write_text(content, encoding="utf-8")
        return path

    def test_imports_hdfc_csv_sanitizes_and_deletes_temporary_file(self) -> None:
        source = self._write_csv("hdfc.csv", HDFC_CSV)

        summary = self.service.import_csv(ImportRequest(user_id=self.user_id, source_path=source))

        self.assertEqual(summary.status, ImportStatus.COMPLETED)
        self.assertEqual(summary.detected_bank, "hdfc")
        self.assertEqual(summary.imported_transactions, 3)
        self.assertEqual(summary.failed_rows, 1)
        self.assertEqual(summary.duplicate_rows, 0)
        self.assertTrue(any(action.action == "deleted_temporary_statement" for action in summary.privacy_actions))
        self.assertEqual(list(self.temp_root.glob("*.csv")), [])
        stored_descriptions = [tx.sanitized_description for tx in self.repository.transactions.values()]
        combined = " ".join(stored_descriptions)
        self.assertNotIn("9876543210", combined)
        self.assertNotIn("123456789012", combined)
        self.assertNotIn("HDFC0001234", combined)
        self.assertIn("[UPI_REDACTED]", combined)
        self.assertIn("[ACCOUNT_REDACTED]", combined)

    def test_duplicate_import_does_not_create_duplicate_transactions(self) -> None:
        source = self._write_csv("hdfc.csv", HDFC_CSV)

        first = self.service.import_csv(ImportRequest(user_id=self.user_id, source_path=source))
        second = self.service.import_csv(ImportRequest(user_id=self.user_id, source_path=source))

        self.assertEqual(first.imported_transactions, 3)
        self.assertEqual(second.imported_transactions, 0)
        self.assertEqual(second.duplicate_rows, 4)
        self.assertEqual(len(self.repository.transactions), 3)

    def test_archive_mode_encrypts_statement_and_removes_clear_temp_file(self) -> None:
        source = self._write_csv("generic.csv", GENERIC_CSV)

        summary = self.service.import_csv(
            ImportRequest(user_id=self.user_id, source_path=source, privacy_mode=PrivacyMode.ARCHIVE)
        )

        self.assertEqual(summary.status, ImportStatus.COMPLETED)
        self.assertIsNotNone(summary.archive_path)
        archive_path = Path(summary.archive_path or "")
        self.assertTrue(archive_path.exists())
        self.assertNotEqual(archive_path.read_text(encoding="utf-8", errors="ignore"), GENERIC_CSV)
        self.assertEqual(list(self.temp_root.glob("*.csv")), [])

    def test_unsupported_file_fails_with_user_safe_message(self) -> None:
        source = self.root / "statement.txt"
        source.write_text("not a csv", encoding="utf-8")

        summary = self.service.import_csv(ImportRequest(user_id=self.user_id, source_path=source))

        self.assertEqual(summary.status, ImportStatus.FAILED)
        self.assertEqual(summary.imported_transactions, 0)
        self.assertIn("CSV", summary.user_message or "")

    def test_generic_csv_fallback_imports_supported_shape(self) -> None:
        source = self._write_csv("generic.csv", GENERIC_CSV)

        summary = self.service.import_csv(ImportRequest(user_id=self.user_id, source_path=source))

        self.assertEqual(summary.detected_bank, "generic_csv")
        self.assertEqual(summary.imported_transactions, 2)
        merchants = {tx.merchant for tx in self.repository.transactions.values()}
        self.assertIn("Grocery Store", merchants)
        self.assertIn("Salary", merchants)

    def test_sqlite_repository_persists_only_sanitized_descriptions(self) -> None:
        db_path = self.root / "tally.db"
        repository = SQLiteImportRepository(db_path)
        service = build_default_import_service(repository, self.file_manager)
        source = self._write_csv("hdfc.csv", HDFC_CSV)

        summary = service.import_csv(ImportRequest(user_id=self.user_id, source_path=source))

        self.assertEqual(summary.imported_transactions, 3)
        import sqlite3

        with closing(sqlite3.connect(db_path)) as conn:
            rows = conn.execute("select description, sanitized_description from transactions").fetchall()
        combined = " ".join(" ".join(row) for row in rows)
        self.assertNotIn("9876543210", combined)
        self.assertNotIn("HDFC0001234", combined)


class ComponentTestCase(unittest.TestCase):
    def test_privacy_engine_redacts_sensitive_values(self) -> None:
        result = PrivacyEngine().sanitize_description(
            "Paid account no 123456789012 via athar@upi IFSC HDFC0001234 Branch MG Road phone 9876543210"
        )

        self.assertIn("ACCOUNT", result.redactions)
        self.assertIn("UPI", result.redactions)
        self.assertIn("IFSC", result.redactions)
        self.assertIn("PHONE", result.redactions)
        self.assertIn("BRANCH", result.redactions)
        self.assertNotIn("9876543210", result.sanitized_description)

    def test_bank_detector_returns_unknown_for_unsupported_headers(self) -> None:
        result = BankDetector().detect("foo,bar,baz\n1,2,3\n")

        self.assertFalse(result.supported)
        self.assertEqual(result.bank_code, "unknown")

    def test_parser_factory_uses_generic_for_unknown_bank_code(self) -> None:
        parser = StatementParserFactory().for_bank("future_pdf_bank")

        parsed = parser.parse(GENERIC_CSV)

        self.assertEqual(len(parsed.rows), 2)

    def test_merchant_resolver_returns_unknown_when_only_redactions_remain(self) -> None:
        merchant = MerchantResolver().resolve("[ACCOUNT_REDACTED] [UPI_REDACTED]")

        self.assertEqual(merchant, MerchantResolver.UNKNOWN_MERCHANT)


if __name__ == "__main__":
    unittest.main()
