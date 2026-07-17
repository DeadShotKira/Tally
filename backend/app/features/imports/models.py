from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, date
from decimal import Decimal
from enum import Enum
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4


class PrivacyMode(str, Enum):
    MAXIMUM_PRIVACY = "maximum_privacy"
    CLOUD_SYNC = "cloud_sync"
    ARCHIVE = "archive"


class TransactionDirection(str, Enum):
    DEBIT = "debit"
    CREDIT = "credit"


class ImportStatus(str, Enum):
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(frozen=True)
class ImportRequest:
    user_id: UUID
    source_path: Path
    privacy_mode: PrivacyMode = PrivacyMode.MAXIMUM_PRIVACY
    original_filename: str | None = None


@dataclass(frozen=True)
class TemporaryStatement:
    path: Path
    original_filename: str
    size_bytes: int
    sha256: str


@dataclass(frozen=True)
class BankDetectionResult:
    bank_code: str
    display_name: str
    confidence: float
    reasons: tuple[str, ...] = ()
    supported: bool = True


@dataclass(frozen=True)
class ParsedTransactionRow:
    row_number: int
    raw_date: str | None
    raw_description: str | None
    raw_debit: str | None = None
    raw_credit: str | None = None
    raw_amount: str | None = None
    raw_direction: str | None = None
    raw_balance: str | None = None
    raw_reference: str | None = None
    raw_notes: str | None = None
    raw_data: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class ParsedStatement:
    rows: tuple[ParsedTransactionRow, ...]
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class ValidationIssue:
    row_number: int | None
    code: str
    message: str
    field: str | None = None


@dataclass(frozen=True)
class ValidationReport:
    warnings: tuple[ValidationIssue, ...] = ()
    errors: tuple[ValidationIssue, ...] = ()

    @property
    def error_count(self) -> int:
        return len(self.errors)

    @property
    def warning_count(self) -> int:
        return len(self.warnings)


@dataclass(frozen=True)
class NormalizedTransaction:
    id: UUID
    user_id: UUID
    import_id: UUID
    date: date
    description: str
    sanitized_description: str
    amount: Decimal
    direction: TransactionDirection
    balance: Decimal | None
    merchant: str
    category: str | None
    reference_number: str | None
    notes: str | None
    tags: tuple[str, ...]
    dedupe_key: str
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class NormalizedCandidate:
    row_number: int
    date: date
    description: str
    amount: Decimal
    direction: TransactionDirection
    balance: Decimal | None
    reference_number: str | None
    notes: str | None


@dataclass(frozen=True)
class ImportRecord:
    id: UUID
    user_id: UUID
    filename: str
    file_hash: str
    detected_bank: str
    privacy_mode: PrivacyMode
    started_at: datetime
    completed_at: datetime | None = None
    status: ImportStatus | None = None
    transaction_count: int = 0
    validation_error_count: int = 0
    validation_warning_count: int = 0
    processing_duration_ms: int = 0
    archive_path: str | None = None

    @classmethod
    def start(
        cls,
        *,
        user_id: UUID,
        filename: str,
        file_hash: str,
        detected_bank: str,
        privacy_mode: PrivacyMode,
    ) -> "ImportRecord":
        return cls(
            id=uuid4(),
            user_id=user_id,
            filename=filename,
            file_hash=file_hash,
            detected_bank=detected_bank,
            privacy_mode=privacy_mode,
            started_at=datetime.now(UTC),
        )


@dataclass(frozen=True)
class PrivacyResult:
    sanitized_description: str
    redactions: tuple[str, ...] = ()


@dataclass(frozen=True)
class PrivacyAction:
    action: str
    details: str


@dataclass(frozen=True)
class ImportSummary:
    import_id: UUID | None
    status: ImportStatus
    detected_bank: str | None
    imported_transactions: int
    failed_rows: int
    duplicate_rows: int
    validation_warnings: tuple[ValidationIssue, ...]
    validation_errors: tuple[ValidationIssue, ...]
    privacy_actions: tuple[PrivacyAction, ...]
    processing_duration_ms: int
    archive_path: str | None = None
    user_message: str | None = None
    technical_details: dict[str, Any] = field(default_factory=dict)
