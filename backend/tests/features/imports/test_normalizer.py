"""Unit tests for the TransactionNormalizer."""

import unittest
from datetime import date
from decimal import Decimal
from backend.app.features.imports.normalizer import TransactionNormalizer
from backend.app.features.imports.models import ParsedTransactionRow, TransactionDirection


class TestTransactionNormalizer(unittest.TestCase):
    def setUp(self) -> None:
        self.normalizer = TransactionNormalizer()

    def test_normalize_valid_row_debit(self) -> None:
        row = ParsedTransactionRow(
            row_number=1,
            raw_date="2026-07-17",
            raw_description="Amazon Purchase",
            raw_debit="450.50",
            raw_credit="",
        )
        candidate, errors = self.normalizer.normalize(row)
        self.assertEqual(len(errors), 0)
        self.assertIsNotNone(candidate)
        self.assertEqual(candidate.date, date(2026, 7, 17))
        self.assertEqual(candidate.description, "Amazon Purchase")
        self.assertEqual(candidate.amount, Decimal("450.50"))
        self.assertEqual(candidate.direction, TransactionDirection.DEBIT)

    def test_normalize_valid_row_credit(self) -> None:
        row = ParsedTransactionRow(
            row_number=2,
            raw_date="17-07-2026",
            raw_description="Salary Credit",
            raw_debit="",
            raw_credit="50000.00",
        )
        candidate, errors = self.normalizer.normalize(row)
        self.assertEqual(len(errors), 0)
        self.assertIsNotNone(candidate)
        self.assertEqual(candidate.date, date(2026, 7, 17))
        self.assertEqual(candidate.amount, Decimal("50000.00"))
        self.assertEqual(candidate.direction, TransactionDirection.CREDIT)

    def test_normalize_different_date_formats(self) -> None:
        formats = [
            ("2026-07-17", date(2026, 7, 17)),
            ("17-07-2026", date(2026, 7, 17)),
            ("17/07/2026", date(2026, 7, 17)),
            ("17/07/26", date(2026, 7, 17)),
            ("17 Jul 2026", date(2026, 7, 17)),
            ("17-Jul-2026", date(2026, 7, 17)),
        ]
        for raw_date, expected_date in formats:
            row = ParsedTransactionRow(
                row_number=3,
                raw_date=raw_date,
                raw_description="Test Row",
                raw_amount="100.00",
                raw_direction="debit",
            )
            candidate, errors = self.normalizer.normalize(row)
            self.assertEqual(len(errors), 0, f"Failed on date format: {raw_date}")
            self.assertIsNotNone(candidate)
            self.assertEqual(candidate.date, expected_date)

    def test_normalize_amount_parsing(self) -> None:
        amounts = [
            ("Rs. 1,234.56", Decimal("1234.56")),
            ("INR 12,000", Decimal("12000.00")),
            ("(500.00)", Decimal("500.00")),  # Treated as debit/credit absolute val
        ]
        for raw_amount, expected_val in amounts:
            row = ParsedTransactionRow(
                row_number=4,
                raw_date="2026-07-17",
                raw_description="Test Amount",
                raw_amount=raw_amount,
                raw_direction="credit",
            )
            candidate, errors = self.normalizer.normalize(row)
            self.assertEqual(len(errors), 0, f"Failed on amount: {raw_amount}")
            self.assertIsNotNone(candidate)
            self.assertEqual(candidate.amount, expected_val)

    def test_normalize_invalid_data(self) -> None:
        # Invalid date
        row = ParsedTransactionRow(
            row_number=5,
            raw_date="invalid-date",
            raw_description="Test",
            raw_debit="10.00",
        )
        candidate, errors = self.normalizer.normalize(row)
        self.assertIsNone(candidate)
        self.assertTrue(any(e.code == "invalid_date" for e in errors))

        # Missing description
        row = ParsedTransactionRow(
            row_number=6,
            raw_date="2026-07-17",
            raw_description="",
            raw_debit="10.00",
        )
        candidate, errors = self.normalizer.normalize(row)
        self.assertIsNone(candidate)
        self.assertTrue(any(e.code == "missing_description" for e in errors))

    def test_dedupe_key_stability(self) -> None:
        row = ParsedTransactionRow(
            row_number=7,
            raw_date="2026-07-17",
            raw_description="Amazon India",
            raw_debit="999.00",
        )
        candidate, _ = self.normalizer.normalize(row)
        self.assertIsNotNone(candidate)

        key1 = self.normalizer.dedupe_key_for(candidate, "amazon india")
        key2 = self.normalizer.dedupe_key_for(candidate, "amazon india")
        self.assertEqual(key1, key2)

        # Different description should yield different key
        key3 = self.normalizer.dedupe_key_for(candidate, "different description")
        self.assertNotEqual(key1, key3)


if __name__ == "__main__":
    unittest.main()
