"""Duplicate detection for the CSV import pipeline.

Provides two-tier deduplication:

1. **File-level**: a SHA-256 hash of the entire CSV file is compared against
   previously imported hashes.  If the file has been imported before, the
   import is short-circuited immediately.

2. **Row-level**: each normalised transaction has a deterministic
   ``dedupe_key`` (SHA-256 of date, amount, direction, sanitized description,
   balance, and reference).  Rows whose keys already exist in the database are
   silently skipped.
"""

from __future__ import annotations

from collections.abc import Iterable

from .models import NormalizedTransaction
from .repository import ImportRepository


class DuplicateDetector:
    def __init__(self, repository: ImportRepository):
        self.repository = repository

    def file_already_imported(self, *, user_id, file_hash: str) -> bool:
        return self.repository.import_exists(user_id=user_id, file_hash=file_hash)

    def split_new_transactions(
        self, *, user_id, transactions: Iterable[NormalizedTransaction]
    ) -> tuple[tuple[NormalizedTransaction, ...], tuple[NormalizedTransaction, ...]]:
        existing = self.repository.existing_dedupe_keys(user_id=user_id, dedupe_keys=[tx.dedupe_key for tx in transactions])
        new: list[NormalizedTransaction] = []
        duplicates: list[NormalizedTransaction] = []
        for transaction in transactions:
            if transaction.dedupe_key in existing:
                duplicates.append(transaction)
            else:
                new.append(transaction)
        return tuple(new), tuple(duplicates)
