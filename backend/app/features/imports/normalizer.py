from __future__ import annotations

import hashlib
import re
from datetime import datetime
from decimal import Decimal, InvalidOperation

from .models import NormalizedCandidate, ParsedTransactionRow, TransactionDirection, ValidationIssue


class TransactionNormalizer:
    DATE_FORMATS = ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%d/%m/%y", "%d %b %Y", "%d-%b-%Y")

    def normalize(self, row: ParsedTransactionRow) -> tuple[NormalizedCandidate | None, tuple[ValidationIssue, ...]]:
        errors: list[ValidationIssue] = []
        parsed_date = self._parse_date(row.raw_date)
        if parsed_date is None:
            errors.append(ValidationIssue(row.row_number, "invalid_date", "Transaction date is missing or invalid.", "date"))

        description = (row.raw_description or "").strip()
        if not description:
            errors.append(ValidationIssue(row.row_number, "missing_description", "Description is required.", "description"))

        amount, direction = self._parse_amount_and_direction(row)
        if amount is None or direction is None:
            errors.append(ValidationIssue(row.row_number, "invalid_amount", "Amount is missing or malformed.", "amount"))

        balance = self._parse_decimal(row.raw_balance)
        if row.raw_balance and balance is None:
            errors.append(ValidationIssue(row.row_number, "invalid_balance", "Balance is malformed.", "balance"))

        if errors:
            return None, tuple(errors)

        return (
            NormalizedCandidate(
                row_number=row.row_number,
                date=parsed_date,
                description=description,
                amount=amount.copy_abs(),
                direction=direction,
                balance=balance,
                reference_number=(row.raw_reference or "").strip() or None,
                notes=(row.raw_notes or "").strip() or None,
            ),
            (),
        )

    def dedupe_key_for(self, candidate: NormalizedCandidate, sanitized_description: str) -> str:
        basis = "|".join(
            [
                candidate.date.isoformat(),
                str(candidate.amount),
                candidate.direction.value,
                sanitized_description.lower(),
                str(candidate.balance or ""),
                candidate.reference_number or "",
            ]
        )
        return hashlib.sha256(basis.encode("utf-8")).hexdigest()

    def _parse_date(self, value: str | None):
        if not value:
            return None
        cleaned = value.strip()
        for fmt in self.DATE_FORMATS:
            try:
                return datetime.strptime(cleaned, fmt).date()
            except ValueError:
                continue
        return None

    def _parse_amount_and_direction(
        self, row: ParsedTransactionRow
    ) -> tuple[Decimal | None, TransactionDirection | None]:
        debit = self._parse_decimal(row.raw_debit)
        credit = self._parse_decimal(row.raw_credit)
        if debit and debit != 0:
            return debit.copy_abs(), TransactionDirection.DEBIT
        if credit and credit != 0:
            return credit.copy_abs(), TransactionDirection.CREDIT

        amount = self._parse_decimal(row.raw_amount)
        if amount is None:
            return None, None
        direction_text = (row.raw_direction or "").strip().lower()
        if direction_text in {"debit", "dr", "withdrawal"} or amount < 0:
            return amount.copy_abs(), TransactionDirection.DEBIT
        if direction_text in {"credit", "cr", "deposit"} or amount > 0:
            return amount.copy_abs(), TransactionDirection.CREDIT
        return None, None

    @staticmethod
    def _parse_decimal(value: str | None) -> Decimal | None:
        if value is None or not value.strip():
            return None
        cleaned = value.strip().replace(",", "")
        cleaned = re.sub(r"(?i)\b(inr|rs\.?|cr|dr)\b", "", cleaned).strip()
        if cleaned.startswith("(") and cleaned.endswith(")"):
            cleaned = "-" + cleaned[1:-1]
        try:
            return Decimal(cleaned)
        except InvalidOperation:
            return None
