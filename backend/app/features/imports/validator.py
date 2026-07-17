"""Post-normalization validation for transaction candidates.

Applies business-rule checks to :class:`NormalizedCandidate` objects *after*
parsing and normalization.  Errors from this stage indicate rows that pass
parsing but violate business constraints (zero amount, absurd balance, etc.).

This is intentionally separate from the parser so each concern can be tested
and changed independently.
"""

from __future__ import annotations

from decimal import Decimal

from .models import NormalizedCandidate, ValidationIssue, ValidationReport


class TransactionValidator:
    """Validate a batch of normalized candidates and return warnings/errors."""

    def validate_candidates(self, candidates: tuple[NormalizedCandidate, ...]) -> ValidationReport:
        """Run all validation rules against *candidates*.

        Args:
            candidates: Tuple of normalized transaction candidates.

        Returns:
            :class:`ValidationReport` containing any warnings and errors.
            Warnings do not block import; errors should prevent the row from
            being persisted.
        """
        warnings: list[ValidationIssue] = []
        errors: list[ValidationIssue] = []
        seen_rows: set[tuple[str, str, str, str]] = set()
        for candidate in candidates:
            if candidate.amount <= Decimal("0"):
                errors.append(ValidationIssue(candidate.row_number, "non_positive_amount", "Amount must be greater than zero.", "amount"))
            if len(candidate.description) > 500:
                warnings.append(ValidationIssue(candidate.row_number, "long_description", "Description was unusually long.", "description"))
            if candidate.balance is not None and abs(candidate.balance) > Decimal("999999999999.99"):
                warnings.append(ValidationIssue(candidate.row_number, "unusual_balance", "Balance appears unusually large.", "balance"))
            key = (
                candidate.date.isoformat(),
                str(candidate.amount),
                candidate.direction.value,
                candidate.description.lower(),
            )
            if key in seen_rows:
                warnings.append(ValidationIssue(candidate.row_number, "duplicate_row_in_file", "This row duplicates another row in the file."))
            seen_rows.add(key)
        return ValidationReport(warnings=tuple(warnings), errors=tuple(errors))
