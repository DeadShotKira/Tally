"""Unit tests for the TransactionValidator."""

import unittest
from datetime import date
from decimal import Decimal

from backend.app.features.imports.models import (
    NormalizedCandidate,
    TransactionDirection,
)
from backend.app.features.imports.validator import TransactionValidator


def _make_candidate(
    *,
    row_number: int = 1,
    desc: str = "Coffee Shop",
    amount: Decimal = Decimal("150.00"),
    direction: TransactionDirection = TransactionDirection.DEBIT,
    balance: Decimal | None = None,
    reference_number: str | None = None,
    notes: str | None = None,
    posted_date: date | None = None,
) -> NormalizedCandidate:
    return NormalizedCandidate(
        row_number=row_number,
        date=posted_date or date(2026, 7, 17),
        description=desc,
        amount=amount,
        direction=direction,
        balance=balance,
        reference_number=reference_number,
        notes=notes,
    )


class TestTransactionValidator(unittest.TestCase):
    def setUp(self) -> None:
        self.validator = TransactionValidator()

    def test_valid_candidates_produce_no_issues(self) -> None:
        candidates = (
            _make_candidate(row_number=1, amount=Decimal("500.00")),
            _make_candidate(row_number=2, amount=Decimal("12000.00"), direction=TransactionDirection.CREDIT),
        )
        report = self.validator.validate_candidates(candidates)
        self.assertEqual(report.error_count, 0)
        self.assertEqual(report.warning_count, 0)

    def test_zero_amount_is_an_error(self) -> None:
        candidates = (_make_candidate(amount=Decimal("0.00")),)
        report = self.validator.validate_candidates(candidates)
        self.assertEqual(report.error_count, 1)
        self.assertTrue(any(e.code == "non_positive_amount" for e in report.errors))

    def test_negative_amount_is_an_error(self) -> None:
        candidates = (_make_candidate(amount=Decimal("-50.00")),)
        report = self.validator.validate_candidates(candidates)
        self.assertTrue(any(e.code == "non_positive_amount" for e in report.errors))

    def test_long_description_is_a_warning(self) -> None:
        candidates = (_make_candidate(desc="A" * 501),)
        report = self.validator.validate_candidates(candidates)
        self.assertEqual(report.error_count, 0)
        self.assertTrue(any(w.code == "long_description" for w in report.warnings))

    def test_description_exactly_500_chars_is_ok(self) -> None:
        candidates = (_make_candidate(desc="A" * 500),)
        report = self.validator.validate_candidates(candidates)
        self.assertFalse(any(w.code == "long_description" for w in report.warnings))

    def test_unusual_balance_is_a_warning(self) -> None:
        candidates = (_make_candidate(balance=Decimal("9999999999999.99")),)
        report = self.validator.validate_candidates(candidates)
        self.assertTrue(any(w.code == "unusual_balance" for w in report.warnings))

    def test_normal_balance_is_ok(self) -> None:
        candidates = (_make_candidate(balance=Decimal("250000.00")),)
        report = self.validator.validate_candidates(candidates)
        self.assertFalse(any(w.code == "unusual_balance" for w in report.warnings))

    def test_duplicate_row_in_file_is_a_warning(self) -> None:
        row = _make_candidate(row_number=1)
        duplicate = _make_candidate(row_number=2)  # same date, amount, direction, desc
        candidates = (row, duplicate)
        report = self.validator.validate_candidates(candidates)
        self.assertTrue(any(w.code == "duplicate_row_in_file" for w in report.warnings))

    def test_different_rows_no_duplicate_warning(self) -> None:
        row1 = _make_candidate(row_number=1, amount=Decimal("100.00"))
        row2 = _make_candidate(row_number=2, amount=Decimal("200.00"))
        candidates = (row1, row2)
        report = self.validator.validate_candidates(candidates)
        self.assertFalse(any(w.code == "duplicate_row_in_file" for w in report.warnings))

    def test_empty_candidates_produces_no_issues(self) -> None:
        report = self.validator.validate_candidates(())
        self.assertEqual(report.error_count, 0)
        self.assertEqual(report.warning_count, 0)


if __name__ == "__main__":
    unittest.main()
