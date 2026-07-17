from __future__ import annotations

import unittest
from datetime import date
from decimal import Decimal
from uuid import uuid4

from backend.app.features.imports.models import TransactionDirection
from backend.app.features.transactions.models import (
    GroupBy,
    SortOption,
    TimelineQuery,
    Transaction,
    TransactionEdit,
    TransactionFilters,
)
from backend.app.features.transactions.repository import InMemoryFinanceRepository
from backend.app.features.transactions.services import AnalyticsService, MerchantService, TimelineService, TransactionService


class FinanceFeatureTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.user_id = uuid4()
        self.other_user_id = uuid4()
        self.import_id = uuid4()
        self.repository = InMemoryFinanceRepository()
        self._seed()
        self.timeline = TimelineService(self.repository)
        self.transactions = TransactionService(self.repository)
        self.merchants = MerchantService(self.repository, self.repository)
        self.analytics = AnalyticsService(self.repository, self.merchants)

    def _seed(self) -> None:
        rows = (
            Transaction.create(
                user_id=self.user_id,
                import_id=self.import_id,
                posted_date=date(2026, 7, 1),
                merchant="Metro Mart",
                description="UPI Metro Mart",
                amount=Decimal("250.00"),
                direction=TransactionDirection.DEBIT,
                category="Groceries",
                tags=("home", "essentials"),
                notes="weekly supplies",
                balance=Decimal("10000.00"),
                reference_number="R1",
            ),
            Transaction.create(
                user_id=self.user_id,
                import_id=self.import_id,
                posted_date=date(2026, 7, 2),
                merchant="Acme Corp",
                description="Salary",
                amount=Decimal("50000.00"),
                direction=TransactionDirection.CREDIT,
                category="Income",
                tags=("salary",),
            ),
            Transaction.create(
                user_id=self.user_id,
                import_id=self.import_id,
                posted_date=date(2026, 7, 3),
                merchant="Cafe Blue",
                description="Card Cafe Blue",
                amount=Decimal("450.00"),
                direction=TransactionDirection.DEBIT,
                category="Dining",
                tags=("food",),
            ),
            Transaction.create(
                user_id=self.user_id,
                import_id=self.import_id,
                posted_date=date(2026, 6, 20),
                merchant="Metro Mart",
                description="POS Metro Mart",
                amount=Decimal("600.00"),
                direction=TransactionDirection.DEBIT,
                category="Groceries",
                tags=("home",),
            ),
            Transaction.create(
                user_id=self.user_id,
                import_id=uuid4(),
                posted_date=date(2025, 12, 31),
                merchant="Rent Owner",
                description="Rent",
                amount=Decimal("12000.00"),
                direction=TransactionDirection.DEBIT,
                category="Rent",
                tags=("fixed",),
            ),
            Transaction.create(
                user_id=self.other_user_id,
                posted_date=date(2026, 7, 1),
                merchant="Other User Shop",
                description="Should never appear",
                amount=Decimal("9999.00"),
                direction=TransactionDirection.DEBIT,
            ),
        )
        for row in rows:
            self.repository.save_transaction(row)

    def test_timeline_paginates_and_groups_by_day_newest_first(self) -> None:
        page = self.timeline.page(TimelineQuery(user_id=self.user_id, page_size=2, group_by=GroupBy.DAY))

        self.assertTrue(page.has_more)
        self.assertEqual(page.next_cursor, 2)
        self.assertEqual(page.total_count, 5)
        self.assertEqual(page.groups[0].key, "2026-07-03")
        self.assertEqual(page.groups[0].transactions[0].merchant, "Cafe Blue")

    def test_search_filters_and_sort_work_together(self) -> None:
        filters = TransactionFilters(
            categories=frozenset({"Groceries"}),
            directions=frozenset({TransactionDirection.DEBIT}),
            tags=frozenset({"home"}),
            min_amount=Decimal("200"),
            max_amount=Decimal("700"),
        )

        page = self.timeline.page(
            TimelineQuery(
                user_id=self.user_id,
                search="metro",
                filters=filters,
                sort=SortOption.HIGHEST_AMOUNT,
                page_size=10,
            )
        )

        results = [tx for group in page.groups for tx in group.transactions]
        self.assertEqual([tx.amount for tx in results], [Decimal("600.00"), Decimal("250.00")])

    def test_clear_filters_equivalent_returns_full_timeline(self) -> None:
        page = self.timeline.page(TimelineQuery(user_id=self.user_id, filters=TransactionFilters(), page_size=20))

        self.assertEqual(page.total_count, 5)

    def test_transaction_detail_and_edit_updates_metadata(self) -> None:
        transaction = next(tx for tx in self.repository.list_transactions(user_id=self.user_id) if tx.merchant == "Cafe Blue")

        updated = self.transactions.edit_metadata(
            user_id=self.user_id,
            transaction_id=transaction.id,
            edit=TransactionEdit(category="Restaurants", merchant_alias="Blue Cafe", notes="client snack", tags=("food", "work")),
        )

        self.assertIsNotNone(updated)
        self.assertEqual(updated.category, "Restaurants")
        self.assertEqual(updated.merchant, "Blue Cafe")
        self.assertEqual(updated.notes, "client snack")
        self.assertEqual(updated.tags, ("food", "work"))
        self.assertEqual(updated.amount, Decimal("450.00"))
        self.assertIsNotNone(self.transactions.get_detail(user_id=self.user_id, transaction_id=transaction.id))

    def test_merchant_statistics_include_frequency_and_monthly_spending(self) -> None:
        stats = self.merchants.stats(user_id=self.user_id, merchant_name="Metro Mart")

        self.assertIsNotNone(stats)
        self.assertEqual(stats.transaction_count, 2)
        self.assertEqual(stats.total_spent, Decimal("850.00"))
        self.assertEqual(stats.average_spend, Decimal("425.00"))
        self.assertEqual(stats.highest_transaction, Decimal("600.00"))
        self.assertEqual(stats.lowest_transaction, Decimal("250.00"))
        self.assertEqual(stats.monthly_spending, (("2026-06", Decimal("600.00")), ("2026-07", Decimal("250.00"))))

    def test_dashboard_summary_and_analytics_are_deterministic(self) -> None:
        dashboard = self.analytics.dashboard(user_id=self.user_id, today=date(2026, 7, 17))

        self.assertEqual(dashboard.summary.total_income, Decimal("50000.00"))
        self.assertEqual(dashboard.summary.total_expense, Decimal("13300.00"))
        self.assertEqual(dashboard.summary.net_savings, Decimal("36700.00"))
        self.assertEqual(dashboard.summary.transaction_count, 5)
        self.assertEqual(dashboard.summary.active_merchants, 4)
        self.assertEqual(dashboard.summary.current_month_spending, Decimal("700.00"))
        self.assertEqual(dashboard.top_categories[0].category, "Rent")
        self.assertEqual(dashboard.largest_expenses[0].merchant, "Rent Owner")
        self.assertEqual(dashboard.largest_income[0].merchant, "Acme Corp")

    def test_category_distribution_calculates_percentage_and_tap_filter(self) -> None:
        stats = self.analytics.category_distribution(user_id=self.user_id)
        groceries = next(item for item in stats if item.category == "Groceries")

        self.assertEqual(groceries.total_spent, Decimal("850.00"))
        self.assertEqual(groceries.transaction_count, 2)
        self.assertEqual(groceries.average_transaction, Decimal("425.00"))
        self.assertEqual(groceries.highest_transaction, Decimal("600.00"))
        self.assertEqual(groceries.percentage_of_total_spending, Decimal("6.39"))

        page = self.timeline.page(
            TimelineQuery(user_id=self.user_id, filters=TransactionFilters(categories=frozenset({"Groceries"})))
        )
        self.assertEqual(page.total_count, 2)

    def test_spending_trends_include_daily_weekly_monthly_yearly_rollups(self) -> None:
        trends = self.analytics.spending_trends(user_id=self.user_id)

        self.assertEqual(trends.average_daily_spending, Decimal("3325.00"))
        self.assertEqual(trends.highest_spending_day, ("2025-12-31", Decimal("12000.00")))
        self.assertEqual(trends.lowest_spending_day, ("2026-07-01", Decimal("250.00")))
        self.assertTrue(any(point.period == "2026-07" and point.expense == Decimal("700.00") for point in trends.monthly))
        self.assertTrue(any(point.period == "2025" and point.expense == Decimal("12000.00") for point in trends.yearly))

    def test_missing_transaction_and_missing_merchant_fail_gracefully(self) -> None:
        self.assertIsNone(self.transactions.get_detail(user_id=self.user_id, transaction_id=uuid4()))
        self.assertIsNone(self.merchants.stats(user_id=self.user_id, merchant_name="Missing Merchant"))

    def test_repository_scopes_every_query_by_user(self) -> None:
        page = self.timeline.page(TimelineQuery(user_id=self.user_id, search="Other User Shop", page_size=20))

        self.assertEqual(page.total_count, 0)


if __name__ == "__main__":
    unittest.main()
