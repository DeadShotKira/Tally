from __future__ import annotations

import sqlite3
from abc import ABC, abstractmethod
from contextlib import closing
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

from .errors import RepositoryError
from .models import ImportRecord, ImportStatus, NormalizedTransaction


class ImportRepository(ABC):
    @abstractmethod
    def import_exists(self, *, user_id: UUID, file_hash: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    def existing_dedupe_keys(self, *, user_id: UUID, dedupe_keys: list[str]) -> set[str]:
        raise NotImplementedError

    @abstractmethod
    def save_import(self, record: ImportRecord) -> None:
        raise NotImplementedError

    @abstractmethod
    def save_transactions(self, transactions: tuple[NormalizedTransaction, ...]) -> None:
        raise NotImplementedError

    @abstractmethod
    def complete_import(
        self,
        record: ImportRecord,
        *,
        status: ImportStatus,
        transaction_count: int,
        validation_error_count: int,
        validation_warning_count: int,
        processing_duration_ms: int,
        archive_path: str | None = None,
    ) -> ImportRecord:
        raise NotImplementedError


class InMemoryImportRepository(ImportRepository):
    def __init__(self):
        self.imports: dict[UUID, ImportRecord] = {}
        self.transactions: dict[UUID, NormalizedTransaction] = {}

    def import_exists(self, *, user_id: UUID, file_hash: str) -> bool:
        return any(record.user_id == user_id and record.file_hash == file_hash for record in self.imports.values())

    def existing_dedupe_keys(self, *, user_id: UUID, dedupe_keys: list[str]) -> set[str]:
        wanted = set(dedupe_keys)
        return {
            transaction.dedupe_key
            for transaction in self.transactions.values()
            if transaction.user_id == user_id and transaction.dedupe_key in wanted
        }

    def save_import(self, record: ImportRecord) -> None:
        self.imports[record.id] = record

    def save_transactions(self, transactions: tuple[NormalizedTransaction, ...]) -> None:
        for transaction in transactions:
            self.transactions[transaction.id] = transaction

    def complete_import(
        self,
        record: ImportRecord,
        *,
        status: ImportStatus,
        transaction_count: int,
        validation_error_count: int,
        validation_warning_count: int,
        processing_duration_ms: int,
        archive_path: str | None = None,
    ) -> ImportRecord:
        completed = replace(
            record,
            completed_at=datetime.now(UTC),
            status=status,
            transaction_count=transaction_count,
            validation_error_count=validation_error_count,
            validation_warning_count=validation_warning_count,
            processing_duration_ms=processing_duration_ms,
            archive_path=archive_path,
        )
        self.imports[record.id] = completed
        return completed


class SQLiteImportRepository(ImportRepository):
    """Local durable adapter used until the SQLAlchemy/PostgreSQL adapter is introduced."""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._connect().close()
        self._migrate()

    def import_exists(self, *, user_id: UUID, file_hash: str) -> bool:
        with closing(self._connect()) as conn:
            row = conn.execute(
                "select 1 from imports where user_id = ? and file_hash = ? limit 1",
                (str(user_id), file_hash),
            ).fetchone()
            return row is not None

    def existing_dedupe_keys(self, *, user_id: UUID, dedupe_keys: list[str]) -> set[str]:
        if not dedupe_keys:
            return set()
        placeholders = ",".join("?" for _ in dedupe_keys)
        with closing(self._connect()) as conn:
            rows = conn.execute(
                f"select dedupe_key from transactions where user_id = ? and dedupe_key in ({placeholders})",
                (str(user_id), *dedupe_keys),
            ).fetchall()
            return {row[0] for row in rows}

    def save_import(self, record: ImportRecord) -> None:
        try:
            with closing(self._connect()) as conn:
                conn.execute(
                    """
                    insert into imports(id, user_id, filename, file_hash, detected_bank, privacy_mode, started_at)
                    values (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        str(record.id),
                        str(record.user_id),
                        record.filename,
                        record.file_hash,
                        record.detected_bank,
                        record.privacy_mode.value,
                        record.started_at.isoformat(),
                    ),
                )
                conn.commit()
        except sqlite3.Error as exc:
            raise RepositoryError(technical_detail=str(exc)) from exc

    def save_transactions(self, transactions: tuple[NormalizedTransaction, ...]) -> None:
        try:
            with closing(self._connect()) as conn:
                conn.executemany(
                    """
                    insert into transactions(
                      id, user_id, import_id, posted_date, description, sanitized_description, amount,
                      direction, balance, merchant, category, reference_number, notes, tags, dedupe_key,
                      created_at, updated_at
                    ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    [
                        (
                            str(tx.id),
                            str(tx.user_id),
                            str(tx.import_id),
                            tx.date.isoformat(),
                            tx.sanitized_description,
                            tx.sanitized_description,
                            str(tx.amount),
                            tx.direction.value,
                            str(tx.balance) if tx.balance is not None else None,
                            tx.merchant,
                            tx.category,
                            tx.reference_number,
                            tx.notes,
                            ",".join(tx.tags),
                            tx.dedupe_key,
                            tx.created_at.isoformat(),
                            tx.updated_at.isoformat(),
                        )
                        for tx in transactions
                    ],
                )
                conn.commit()
        except sqlite3.Error as exc:
            raise RepositoryError(technical_detail=str(exc)) from exc

    def complete_import(
        self,
        record: ImportRecord,
        *,
        status: ImportStatus,
        transaction_count: int,
        validation_error_count: int,
        validation_warning_count: int,
        processing_duration_ms: int,
        archive_path: str | None = None,
    ) -> ImportRecord:
        completed = replace(
            record,
            completed_at=datetime.now(UTC),
            status=status,
            transaction_count=transaction_count,
            validation_error_count=validation_error_count,
            validation_warning_count=validation_warning_count,
            processing_duration_ms=processing_duration_ms,
            archive_path=archive_path,
        )
        try:
            with closing(self._connect()) as conn:
                conn.execute(
                    """
                    update imports
                    set completed_at = ?, status = ?, transaction_count = ?, validation_error_count = ?,
                        validation_warning_count = ?, processing_duration_ms = ?, archive_path = ?
                    where id = ?
                    """,
                    (
                        completed.completed_at.isoformat() if completed.completed_at else None,
                        status.value,
                        transaction_count,
                        validation_error_count,
                        validation_warning_count,
                        processing_duration_ms,
                        archive_path,
                        str(record.id),
                    ),
                )
                conn.commit()
        except sqlite3.Error as exc:
            raise RepositoryError(technical_detail=str(exc)) from exc
        return completed

    def _connect(self) -> sqlite3.Connection:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        return sqlite3.connect(self.db_path)

    def _migrate(self) -> None:
        with closing(self._connect()) as conn:
            conn.execute(
                """
                create table if not exists imports (
                  id text primary key,
                  user_id text not null,
                  filename text not null,
                  file_hash text not null,
                  detected_bank text not null,
                  privacy_mode text not null,
                  started_at text not null,
                  completed_at text,
                  status text,
                  transaction_count integer default 0,
                  validation_error_count integer default 0,
                  validation_warning_count integer default 0,
                  processing_duration_ms integer default 0,
                  archive_path text
                )
                """
            )
            conn.execute("create index if not exists ix_imports_user_file on imports(user_id, file_hash)")
            conn.execute(
                """
                create table if not exists transactions (
                  id text primary key,
                  user_id text not null,
                  import_id text not null,
                  posted_date text not null,
                  description text not null,
                  sanitized_description text not null,
                  amount text not null,
                  direction text not null,
                  balance text,
                  merchant text not null,
                  category text,
                  reference_number text,
                  notes text,
                  tags text,
                  dedupe_key text not null,
                  created_at text not null,
                  updated_at text not null
                )
                """
            )
            conn.execute("create unique index if not exists ux_transactions_user_dedupe on transactions(user_id, dedupe_key)")
            conn.commit()
