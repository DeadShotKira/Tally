from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from decimal import Decimal
from enum import Enum
from uuid import UUID, uuid4

from backend.app.features.imports.models import TransactionDirection


class SortOption(str, Enum):
    NEWEST_FIRST = "newest_first"
    OLDEST_FIRST = "oldest_first"
    HIGHEST_AMOUNT = "highest_amount"
    LOWEST_AMOUNT = "lowest_amount"
    MERCHANT = "merchant"
    CATEGORY = "category"


class GroupBy(str, Enum):
    DAY = "day"
    MONTH = "month"
    YEAR = "year"


@dataclass(frozen=True)
class Transaction:
    id: UUID
    user_id: UUID
    import_id: UUID | None
    posted_date: date
    description: str
    amount: Decimal
    direction: TransactionDirection
    balance: Decimal | None
    merchant: str
    category: str | None
    reference_number: str | None
    notes: str | None
    tags: tuple[str, ...]
    created_at: datetime
    updated_at: datetime

    @classmethod
    def create(
        cls,
        *,
        user_id: UUID,
        posted_date: date,
        amount: Decimal,
        direction: TransactionDirection,
        merchant: str,
        description: str = "",
        category: str | None = None,
        tags: tuple[str, ...] = (),
        notes: str | None = None,
        import_id: UUID | None = None,
        balance: Decimal | None = None,
        reference_number: str | None = None,
    ) -> "Transaction":
        now = datetime.now(UTC)
        return cls(
            id=uuid4(),
            user_id=user_id,
            import_id=import_id,
            posted_date=posted_date,
            description=description,
            amount=amount,
            direction=direction,
            balance=balance,
            merchant=merchant,
            category=category,
            reference_number=reference_number,
            notes=notes,
            tags=tags,
            created_at=now,
            updated_at=now,
        )


@dataclass(frozen=True)
class TransactionFilters:
    from_date: date | None = None
    to_date: date | None = None
    categories: frozenset[str] = frozenset()
    merchants: frozenset[str] = frozenset()
    min_amount: Decimal | None = None
    max_amount: Decimal | None = None
    directions: frozenset[TransactionDirection] = frozenset()
    tags: frozenset[str] = frozenset()
    import_ids: frozenset[UUID] = frozenset()

    @property
    def is_empty(self) -> bool:
        return self == TransactionFilters()


@dataclass(frozen=True)
class TimelineQuery:
    user_id: UUID
    search: str | None = None
    filters: TransactionFilters = field(default_factory=TransactionFilters)
    sort: SortOption = SortOption.NEWEST_FIRST
    page_size: int = 50
    cursor: int = 0
    group_by: GroupBy = GroupBy.DAY


@dataclass(frozen=True)
class TimelineGroup:
    key: str
    label: str
    transactions: tuple[Transaction, ...]
    income: Decimal
    expense: Decimal


@dataclass(frozen=True)
class TimelinePage:
    groups: tuple[TimelineGroup, ...]
    total_count: int
    next_cursor: int | None
    has_more: bool


@dataclass(frozen=True)
class TransactionEdit:
    category: str | None = None
    merchant_alias: str | None = None
    notes: str | None = None
    tags: tuple[str, ...] | None = None


@dataclass(frozen=True)
class Merchant:
    id: UUID
    user_id: UUID
    name: str
    aliases: tuple[str, ...] = ()
    category: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass(frozen=True)
class MerchantStats:
    merchant: str
    category: str | None
    first_transaction: date | None
    last_transaction: date | None
    transaction_count: int
    total_spent: Decimal
    average_spend: Decimal
    highest_transaction: Decimal
    lowest_transaction: Decimal
    frequency_per_month: Decimal
    monthly_spending: tuple[tuple[str, Decimal], ...]


@dataclass(frozen=True)
class CategoryStats:
    category: str
    total_spent: Decimal
    transaction_count: int
    average_transaction: Decimal
    highest_transaction: Decimal
    percentage_of_total_spending: Decimal


@dataclass(frozen=True)
class DashboardSummary:
    total_income: Decimal
    total_expense: Decimal
    net_savings: Decimal
    transaction_count: int
    active_merchants: int
    current_month_spending: Decimal


@dataclass(frozen=True)
class TrendPoint:
    period: str
    income: Decimal = Decimal("0")
    expense: Decimal = Decimal("0")
    transaction_count: int = 0


@dataclass(frozen=True)
class SpendingTrendSummary:
    daily: tuple[TrendPoint, ...]
    weekly: tuple[TrendPoint, ...]
    monthly: tuple[TrendPoint, ...]
    yearly: tuple[TrendPoint, ...]
    average_daily_spending: Decimal
    highest_spending_day: tuple[str, Decimal] | None
    lowest_spending_day: tuple[str, Decimal] | None


@dataclass(frozen=True)
class DashboardAnalytics:
    summary: DashboardSummary
    monthly_spending_trend: tuple[TrendPoint, ...]
    monthly_income_trend: tuple[TrendPoint, ...]
    category_distribution: tuple[CategoryStats, ...]
    merchant_spending: tuple[MerchantStats, ...]
    daily_spending: tuple[TrendPoint, ...]
    weekly_spending: tuple[TrendPoint, ...]
    top_categories: tuple[CategoryStats, ...]
    top_merchants: tuple[MerchantStats, ...]
    largest_expenses: tuple[Transaction, ...]
    largest_income: tuple[Transaction, ...]
