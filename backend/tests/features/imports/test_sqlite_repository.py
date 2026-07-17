"""Focused contract tests for the durable SQLite import adapter."""

from __future__ import annotations

import tempfile
import unittest
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

from backend.app.features.imports.models import (
    ImportRecord,
    PrivacyMode,
    NormalizedTransaction,
    TransactionDirection,
)
from backend.app.features.imports.repository import SQLiteImportRepository


class TestSQLiteImportRepository(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "imports.sqlite3"
        self.repository = SQLiteImportRepository(self.db_path)
        self.user_id = uuid4()

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_persists_import_and_finds_user_scoped_dedupe_key(self) -> None:
        record = ImportRecord.start(
            user_id=self.user_id,
            filename="statement.csv",
            file_hash="a" * 64,
            detected_bank="generic_csv",
            privacy_mode=PrivacyMode.MAXIMUM_PRIVACY,
        )
        transaction = NormalizedTransaction(
            id=uuid4(),
            user_id=self.user_id,
            import_id=record.id,
            date=date(2026, 7, 17),
            description="Coffee",
            sanitized_description="Coffee",
            amount=Decimal("120.00"),
            direction=TransactionDirection.DEBIT,
            balance=None,
            merchant="Coffee",
            category=None,
            reference_number=None,
            notes=None,
            tags=(),
            dedupe_key="dedupe-key",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        self.repository.save_import(record)
        self.repository.save_transactions((transaction,))

        self.assertTrue(self.repository.import_exists(user_id=self.user_id, file_hash="a" * 64))
        self.assertEqual(
            self.repository.existing_dedupe_keys(user_id=self.user_id, dedupe_keys=["dedupe-key", "other"]),
            {"dedupe-key"},
        )
        self.assertEqual(
            self.repository.existing_dedupe_keys(user_id=uuid4(), dedupe_keys=["dedupe-key"]),
            set(),
        )
