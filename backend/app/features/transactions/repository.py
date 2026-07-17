"""Repository interfaces and in-memory implementation for transaction and metadata storage.

Defines persistence contracts for transactions, merchants, categories, and tags,
as well as the in-memory implementations used for testing and fast local execution.
"""

from __future__ import annotations


from abc import ABC, abstractmethod
from dataclasses import replace
from datetime import UTC, datetime
from uuid import UUID, uuid4

from backend.app.features.imports.models import NormalizedTransaction

from .models import Merchant, Transaction, TransactionEdit


class TransactionRepository(ABC):
    @abstractmethod
    def list_transactions(self, *, user_id: UUID) -> tuple[Transaction, ...]:
        raise NotImplementedError

    @abstractmethod
    def get_transaction(self, *, user_id: UUID, transaction_id: UUID) -> Transaction | None:
        raise NotImplementedError

    @abstractmethod
    def save_transaction(self, transaction: Transaction) -> None:
        raise NotImplementedError

    @abstractmethod
    def update_transaction_metadata(
        self, *, user_id: UUID, transaction_id: UUID, edit: TransactionEdit
    ) -> Transaction | None:
        raise NotImplementedError


class MerchantRepository(ABC):
    @abstractmethod
    def get_or_create(self, *, user_id: UUID, name: str, category: str | None = None) -> Merchant:
        raise NotImplementedError

    @abstractmethod
    def list_merchants(self, *, user_id: UUID) -> tuple[Merchant, ...]:
        raise NotImplementedError

    @abstractmethod
    def add_alias(self, *, user_id: UUID, merchant_name: str, alias: str) -> Merchant:
        raise NotImplementedError


class CategoryRepository(ABC):
    @abstractmethod
    def list_categories(self, *, user_id: UUID) -> tuple[str, ...]:
        raise NotImplementedError

    @abstractmethod
    def save_category(self, *, user_id: UUID, name: str) -> None:
        raise NotImplementedError


class TagRepository(ABC):
    @abstractmethod
    def list_tags(self, *, user_id: UUID) -> tuple[str, ...]:
        raise NotImplementedError

    @abstractmethod
    def save_tag(self, *, user_id: UUID, name: str) -> None:
        raise NotImplementedError


class InMemoryFinanceRepository(TransactionRepository, MerchantRepository, CategoryRepository, TagRepository):
    def __init__(self):
        self.transactions: dict[UUID, Transaction] = {}
        self.merchants: dict[tuple[UUID, str], Merchant] = {}
        self.categories: dict[UUID, set[str]] = {}
        self.tags: dict[UUID, set[str]] = {}

    @classmethod
    def from_normalized_transactions(
        cls, transactions: tuple[NormalizedTransaction, ...]
    ) -> "InMemoryFinanceRepository":
        repository = cls()
        for normalized in transactions:
            transaction = Transaction(
                id=normalized.id,
                user_id=normalized.user_id,
                import_id=normalized.import_id,
                posted_date=normalized.date,
                description=normalized.sanitized_description,
                amount=normalized.amount,
                direction=normalized.direction,
                balance=normalized.balance,
                merchant=normalized.merchant,
                category=normalized.category,
                reference_number=normalized.reference_number,
                notes=normalized.notes,
                tags=normalized.tags,
                created_at=normalized.created_at,
                updated_at=normalized.updated_at,
            )
            repository.save_transaction(transaction)
        return repository

    def list_transactions(self, *, user_id: UUID) -> tuple[Transaction, ...]:
        return tuple(transaction for transaction in self.transactions.values() if transaction.user_id == user_id)

    def get_transaction(self, *, user_id: UUID, transaction_id: UUID) -> Transaction | None:
        transaction = self.transactions.get(transaction_id)
        if transaction is None or transaction.user_id != user_id:
            return None
        return transaction

    def save_transaction(self, transaction: Transaction) -> None:
        self.transactions[transaction.id] = transaction
        self.get_or_create(user_id=transaction.user_id, name=transaction.merchant, category=transaction.category)
        if transaction.category:
            self.save_category(user_id=transaction.user_id, name=transaction.category)
        for tag in transaction.tags:
            self.save_tag(user_id=transaction.user_id, name=tag)

    def update_transaction_metadata(
        self, *, user_id: UUID, transaction_id: UUID, edit: TransactionEdit
    ) -> Transaction | None:
        transaction = self.get_transaction(user_id=user_id, transaction_id=transaction_id)
        if transaction is None:
            return None
        merchant = edit.merchant_alias.strip() if edit.merchant_alias else transaction.merchant
        category = edit.category if edit.category is not None else transaction.category
        tags = tuple(dict.fromkeys(tag.strip() for tag in edit.tags if tag.strip())) if edit.tags is not None else transaction.tags
        updated = replace(
            transaction,
            merchant=merchant or transaction.merchant,
            category=category,
            notes=edit.notes if edit.notes is not None else transaction.notes,
            tags=tags,
            updated_at=datetime.now(UTC),
        )
        self.save_transaction(updated)
        if edit.merchant_alias:
            self.add_alias(user_id=user_id, merchant_name=updated.merchant, alias=edit.merchant_alias)
        return updated

    def get_or_create(self, *, user_id: UUID, name: str, category: str | None = None) -> Merchant:
        key = (user_id, self._key(name))
        existing = self.merchants.get(key)
        if existing is not None:
            if category and existing.category != category:
                updated = replace(existing, category=category, updated_at=datetime.now(UTC))
                self.merchants[key] = updated
                return updated
            return existing
        merchant = Merchant(id=uuid4(), user_id=user_id, name=name, category=category)
        self.merchants[key] = merchant
        return merchant

    def list_merchants(self, *, user_id: UUID) -> tuple[Merchant, ...]:
        return tuple(merchant for merchant in self.merchants.values() if merchant.user_id == user_id)

    def add_alias(self, *, user_id: UUID, merchant_name: str, alias: str) -> Merchant:
        merchant = self.get_or_create(user_id=user_id, name=merchant_name)
        aliases = tuple(dict.fromkeys((*merchant.aliases, alias.strip())))
        updated = replace(merchant, aliases=aliases, updated_at=datetime.now(UTC))
        self.merchants[(user_id, self._key(merchant_name))] = updated
        return updated

    def list_categories(self, *, user_id: UUID) -> tuple[str, ...]:
        return tuple(sorted(self.categories.get(user_id, set())))

    def save_category(self, *, user_id: UUID, name: str) -> None:
        cleaned = name.strip()
        if cleaned:
            self.categories.setdefault(user_id, set()).add(cleaned)

    def list_tags(self, *, user_id: UUID) -> tuple[str, ...]:
        return tuple(sorted(self.tags.get(user_id, set())))

    def save_tag(self, *, user_id: UUID, name: str) -> None:
        cleaned = name.strip()
        if cleaned:
            self.tags.setdefault(user_id, set()).add(cleaned)

    @staticmethod
    def _key(value: str) -> str:
        return " ".join(value.lower().split())
