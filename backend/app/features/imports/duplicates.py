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
