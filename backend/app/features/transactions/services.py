"""Services for transactions timeline, management, and analytics dashboard.

Handles transaction querying, pagination, grouping, metadata editing,
merchant statistics calculation, and financial summary generation.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import replace
from datetime import UTC, date, datetime
from decimal import Decimal, ROUND_HALF_UP
from uuid import UUID

from backend.app.features.imports.models import TransactionDirection

from .logging import SafeFinanceLogger
from .models import (
    CategoryStats,
    DashboardAnalytics,
    DashboardSummary,
    GroupBy,
    MerchantStats,
    SortOption,
    SpendingTrendSummary,
    TimelineGroup,
    TimelinePage,
    TimelineQuery,
    Transaction,
    TransactionEdit,
    TransactionFilters,
    TrendPoint,
)
from .repository import MerchantRepository, TransactionRepository


ZERO = Decimal("0")
TWOPLACES = Decimal("0.01")
TOP_N = 5


def _sort_oldest_first_key(tx: Transaction) -> tuple[date, datetime, str]:
    return tx.posted_date, tx.created_at, tx.id.hex


def _sort_newest_first_key(tx: Transaction) -> tuple[date, datetime, str]:
    return tx.posted_date, tx.created_at, tx.id.hex


def _sort_highest_amount_key(tx: Transaction) -> tuple[Decimal, date]:
    return -tx.amount, tx.posted_date


def _sort_lowest_amount_key(tx: Transaction) -> tuple[Decimal, date]:
    return tx.amount, tx.posted_date


def _sort_merchant_key(tx: Transaction) -> tuple[str, Decimal]:
    return tx.merchant.lower(), -tx.amount


def _sort_category_key(tx: Transaction) -> tuple[str, str]:
    return (tx.category or "").lower(), tx.merchant.lower()



class TimelineService:
    def __init__(self, repository: TransactionRepository):
        self.repository = repository

    def page(self, query: TimelineQuery) -> TimelinePage:
        page_size = max(1, min(query.page_size, 200))
        cursor = max(0, query.cursor)
        transactions = self.repository.list_transactions(user_id=query.user_id)
        filtered = self._apply_filters(transactions, query.filters)
        searched = self._apply_search(filtered, query.search)
        sorted_transactions = self._sort(searched, query.sort)
        page_items = sorted_transactions[cursor : cursor + page_size]
        next_cursor = cursor + page_size if cursor + page_size < len(sorted_transactions) else None
        return TimelinePage(
            groups=self._group(page_items, query.group_by),
            total_count=len(sorted_transactions),
            next_cursor=next_cursor,
            has_more=next_cursor is not None,
        )

    def _apply_filters(
        self, transactions: tuple[Transaction, ...], filters: TransactionFilters
    ) -> tuple[Transaction, ...]:
        if filters.is_empty:
            return transactions
        result: list[Transaction] = []
        for transaction in transactions:
            if filters.from_date and transaction.posted_date < filters.from_date:
                continue
            if filters.to_date and transaction.posted_date > filters.to_date:
                continue
            if filters.categories and (transaction.category or "") not in filters.categories:
                continue
            if filters.merchants and transaction.merchant not in filters.merchants:
                continue
            if filters.min_amount is not None and transaction.amount < filters.min_amount:
                continue
            if filters.max_amount is not None and transaction.amount > filters.max_amount:
                continue
            if filters.directions and transaction.direction not in filters.directions:
                continue
            if filters.tags and not filters.tags.intersection(transaction.tags):
                continue
            if filters.import_ids and transaction.import_id not in filters.import_ids:
                continue
            result.append(transaction)
        return tuple(result)

    def _apply_search(self, transactions: tuple[Transaction, ...], search: str | None) -> tuple[Transaction, ...]:
        if not search or not search.strip():
            return transactions
        needle = search.strip().lower()
        result = []
        for transaction in transactions:
            haystack = " ".join(
                [
                    transaction.merchant,
                    transaction.description,
                    transaction.notes or "",
                    transaction.category or "",
                    " ".join(transaction.tags),
                    str(transaction.amount),
                ]
            ).lower()
            if needle in haystack:
                result.append(transaction)
        return tuple(result)

    def _sort(self, transactions: tuple[Transaction, ...], sort: SortOption) -> tuple[Transaction, ...]:
        if sort == SortOption.OLDEST_FIRST:
            return tuple(sorted(transactions, key=_sort_oldest_first_key))
        if sort == SortOption.HIGHEST_AMOUNT:
            return tuple(sorted(transactions, key=_sort_highest_amount_key))
        if sort == SortOption.LOWEST_AMOUNT:
            return tuple(sorted(transactions, key=_sort_lowest_amount_key))
        if sort == SortOption.MERCHANT:
            return tuple(sorted(transactions, key=_sort_merchant_key))
        if sort == SortOption.CATEGORY:
            return tuple(sorted(transactions, key=_sort_category_key))
        return tuple(sorted(transactions, key=_sort_newest_first_key, reverse=True))

    def _group(self, transactions: tuple[Transaction, ...], group_by: GroupBy) -> tuple[TimelineGroup, ...]:
        buckets: dict[str, list[Transaction]] = defaultdict(list)
        for transaction in transactions:
            key = self._group_key(transaction.posted_date, group_by)
            buckets[key].append(transaction)
        groups = []
        for key, items in buckets.items():
            income = sum((tx.amount for tx in items if tx.direction == TransactionDirection.CREDIT), ZERO)
            expense = sum((tx.amount for tx in items if tx.direction == TransactionDirection.DEBIT), ZERO)
            groups.append(TimelineGroup(key=key, label=key, transactions=tuple(items), income=income, expense=expense))
        return tuple(groups)

    @staticmethod
    def _group_key(value: date, group_by: GroupBy) -> str:
        if group_by == GroupBy.YEAR:
            return value.strftime("%Y")
        if group_by == GroupBy.MONTH:
            return value.strftime("%Y-%m")
        return value.isoformat()


class TransactionService:
    def __init__(self, repository: TransactionRepository, logger: SafeFinanceLogger | None = None):
        self.repository = repository
        self.logger = logger or SafeFinanceLogger()

    def get_detail(self, *, user_id: UUID, transaction_id: UUID) -> Transaction | None:
        return self.repository.get_transaction(user_id=user_id, transaction_id=transaction_id)

    def edit_metadata(self, *, user_id: UUID, transaction_id: UUID, edit: TransactionEdit) -> Transaction | None:
        updated = self.repository.update_transaction_metadata(user_id=user_id, transaction_id=transaction_id, edit=edit)
        if updated is not None:
            self.logger.info("transaction_metadata_updated", user_id=str(user_id), transaction_id=str(transaction_id))
        return updated


class MerchantService:
    def __init__(self, transaction_repository: TransactionRepository, merchant_repository: MerchantRepository):
        self.transaction_repository = transaction_repository
        self.merchant_repository = merchant_repository

    def stats(self, *, user_id: UUID, merchant_name: str) -> MerchantStats | None:
        transactions = tuple(
            tx for tx in self.transaction_repository.list_transactions(user_id=user_id) if tx.merchant == merchant_name
        )
        if not transactions:
            return None
        merchant = self.merchant_repository.get_or_create(user_id=user_id, name=merchant_name)
        return _merchant_stats(merchant.name, merchant.category, transactions)

    def all_stats(self, *, user_id: UUID) -> tuple[MerchantStats, ...]:
        transactions = self.transaction_repository.list_transactions(user_id=user_id)
        by_merchant: dict[str, list[Transaction]] = defaultdict(list)
        for transaction in transactions:
            by_merchant[transaction.merchant].append(transaction)
        # Performance optimization: pre-load existing merchants to avoid repeated get_or_create lookups
        existing_merchants = {
            " ".join(m.name.lower().split()): m
            for m in self.merchant_repository.list_merchants(user_id=user_id)
        }
        stats = []
        for merchant_name, items in by_merchant.items():
            key = " ".join(merchant_name.lower().split())
            merchant = existing_merchants.get(key)
            if merchant is None:
                merchant = self.merchant_repository.get_or_create(user_id=user_id, name=merchant_name)
                existing_merchants[key] = merchant
            stats.append(_merchant_stats(merchant.name, merchant.category, tuple(items)))
        return tuple(sorted(stats, key=lambda item: item.total_spent, reverse=True))


class AnalyticsService:
    def __init__(self, transaction_repository: TransactionRepository, merchant_service: MerchantService):
        self.transaction_repository = transaction_repository
        self.merchant_service = merchant_service
        self._dashboard_cache: dict[tuple[UUID, int, datetime], DashboardAnalytics] = {}

    def dashboard(self, *, user_id: UUID, today: date | None = None) -> DashboardAnalytics:
        transactions = self.transaction_repository.list_transactions(user_id=user_id)
        max_updated = max((tx.updated_at for tx in transactions), default=datetime.min)
        cache_key = (user_id, len(transactions), max_updated)
        cached = self._dashboard_cache.get(cache_key)
        if cached is not None:
            return cached
        today = today or datetime.now(UTC).date()
        summary = self.summary(user_id=user_id, today=today)
        category_stats = self.category_distribution(user_id=user_id)
        merchant_stats = self.merchant_service.all_stats(user_id=user_id)
        dashboard = DashboardAnalytics(
            summary=summary,
            monthly_spending_trend=self.trend(user_id=user_id, period="monthly", direction=TransactionDirection.DEBIT),
            monthly_income_trend=self.trend(user_id=user_id, period="monthly", direction=TransactionDirection.CREDIT),
            category_distribution=category_stats,
            merchant_spending=merchant_stats,
            daily_spending=self.trend(user_id=user_id, period="daily", direction=TransactionDirection.DEBIT),
            weekly_spending=self.trend(user_id=user_id, period="weekly", direction=TransactionDirection.DEBIT),
            top_categories=category_stats[:TOP_N],
            top_merchants=merchant_stats[:TOP_N],
            largest_expenses=self.largest(user_id=user_id, direction=TransactionDirection.DEBIT, limit=TOP_N),
            largest_income=self.largest(user_id=user_id, direction=TransactionDirection.CREDIT, limit=TOP_N),
        )
        self._dashboard_cache.clear()
        self._dashboard_cache[cache_key] = dashboard
        return dashboard

    def summary(self, *, user_id: UUID, today: date | None = None) -> DashboardSummary:
        today = today or datetime.now(UTC).date()
        transactions = self.transaction_repository.list_transactions(user_id=user_id)
        total_income = sum((tx.amount for tx in transactions if tx.direction == TransactionDirection.CREDIT), ZERO)
        total_expense = sum((tx.amount for tx in transactions if tx.direction == TransactionDirection.DEBIT), ZERO)
        current_month_spending = sum(
            (
                tx.amount
                for tx in transactions
                if tx.direction == TransactionDirection.DEBIT
                and tx.posted_date.year == today.year
                and tx.posted_date.month == today.month
            ),
            ZERO,
        )
        return DashboardSummary(
            total_income=total_income,
            total_expense=total_expense,
            net_savings=total_income - total_expense,
            transaction_count=len(transactions),
            active_merchants=len({tx.merchant for tx in transactions}),
            current_month_spending=current_month_spending,
        )

    def category_distribution(self, *, user_id: UUID) -> tuple[CategoryStats, ...]:
        debit_transactions = tuple(
            tx
            for tx in self.transaction_repository.list_transactions(user_id=user_id)
            if tx.direction == TransactionDirection.DEBIT
        )
        total_spending = sum((tx.amount for tx in debit_transactions), ZERO)
        by_category: dict[str, list[Transaction]] = defaultdict(list)
        for transaction in debit_transactions:
            by_category[transaction.category or "Uncategorized"].append(transaction)
        stats = []
        for category, items in by_category.items():
            total = sum((tx.amount for tx in items), ZERO)
            count = len(items)
            stats.append(
                CategoryStats(
                    category=category,
                    total_spent=total,
                    transaction_count=count,
                    average_transaction=_money(total / count) if count else ZERO,
                    highest_transaction=max((tx.amount for tx in items), default=ZERO),
                    percentage_of_total_spending=_money((total / total_spending) * Decimal("100")) if total_spending else ZERO,
                )
            )
        return tuple(sorted(stats, key=lambda item: item.total_spent, reverse=True))

    def trend(
        self, *, user_id: UUID, period: str, direction: TransactionDirection | None = None
    ) -> tuple[TrendPoint, ...]:
        buckets: dict[str, list[Transaction]] = defaultdict(list)
        for transaction in self.transaction_repository.list_transactions(user_id=user_id):
            if direction and transaction.direction != direction:
                continue
            buckets[_period_key(transaction.posted_date, period)].append(transaction)
        points = []
        for key in sorted(buckets):
            items = buckets[key]
            income = sum((tx.amount for tx in items if tx.direction == TransactionDirection.CREDIT), ZERO)
            expense = sum((tx.amount for tx in items if tx.direction == TransactionDirection.DEBIT), ZERO)
            points.append(TrendPoint(period=key, income=income, expense=expense, transaction_count=len(items)))
        return tuple(points)

    def spending_trends(self, *, user_id: UUID) -> SpendingTrendSummary:
        daily = self.trend(user_id=user_id, period="daily", direction=TransactionDirection.DEBIT)
        daily_amounts = [(point.period, point.expense) for point in daily]
        total = sum((amount for _, amount in daily_amounts), ZERO)
        return SpendingTrendSummary(
            daily=daily,
            weekly=self.trend(user_id=user_id, period="weekly", direction=TransactionDirection.DEBIT),
            monthly=self.trend(user_id=user_id, period="monthly", direction=TransactionDirection.DEBIT),
            yearly=self.trend(user_id=user_id, period="yearly", direction=TransactionDirection.DEBIT),
            average_daily_spending=_money(total / len(daily_amounts)) if daily_amounts else ZERO,
            highest_spending_day=max(daily_amounts, key=lambda item: item[1]) if daily_amounts else None,
            lowest_spending_day=min(daily_amounts, key=lambda item: item[1]) if daily_amounts else None,
        )

    def largest(
        self, *, user_id: UUID, direction: TransactionDirection, limit: int
    ) -> tuple[Transaction, ...]:
        transactions = [
            tx for tx in self.transaction_repository.list_transactions(user_id=user_id) if tx.direction == direction
        ]
        return tuple(sorted(transactions, key=lambda tx: tx.amount, reverse=True)[:limit])


def _merchant_stats(merchant_name: str, category: str | None, transactions: tuple[Transaction, ...]) -> MerchantStats:
    debits = tuple(tx for tx in transactions if tx.direction == TransactionDirection.DEBIT)
    spend_source = debits or transactions
    total_spent = sum((tx.amount for tx in debits), ZERO)
    dates = sorted(tx.posted_date for tx in transactions)
    monthly: dict[str, Decimal] = defaultdict(lambda: ZERO)
    for tx in debits:
        monthly[tx.posted_date.strftime("%Y-%m")] += tx.amount
    month_span = _month_span(dates[0], dates[-1]) if dates else 1
    return MerchantStats(
        merchant=merchant_name,
        category=category,
        first_transaction=dates[0] if dates else None,
        last_transaction=dates[-1] if dates else None,
        transaction_count=len(transactions),
        total_spent=total_spent,
        average_spend=_money(total_spent / len(debits)) if debits else ZERO,
        highest_transaction=max((tx.amount for tx in spend_source), default=ZERO),
        lowest_transaction=min((tx.amount for tx in spend_source), default=ZERO),
        frequency_per_month=_money(Decimal(len(transactions)) / Decimal(month_span)),
        monthly_spending=tuple(sorted(monthly.items())),
    )


def _period_key(value: date, period: str) -> str:
    if period == "yearly":
        return value.strftime("%Y")
    if period == "monthly":
        return value.strftime("%Y-%m")
    if period == "weekly":
        year, week, _ = value.isocalendar()
        return f"{year}-W{week:02d}"
    return value.isoformat()


def _month_span(start: date, end: date) -> int:
    return max(1, ((end.year - start.year) * 12) + end.month - start.month + 1)


def _money(value: Decimal) -> Decimal:
    return value.quantize(TWOPLACES, rounding=ROUND_HALF_UP)
