"""Unit tests for AnalyticsService caching and dashboard correctness."""

import unittest
from datetime import date
from decimal import Decimal
from uuid import uuid4

from backend.app.features.imports.models import TransactionDirection
from backend.app.features.transactions.models import Transaction
from backend.app.features.transactions.repository import InMemoryFinanceRepository
from backend.app.features.transactions.services import AnalyticsService, MerchantService, TOP_N


class TestAnalyticsDashboardCache(unittest.TestCase):
    def setUp(self) -> None:
        self.user_id = uuid4()
        self.repository = InMemoryFinanceRepository()
        merchant_service = MerchantService(self.repository, self.repository)
        self.analytics = AnalyticsService(self.repository, merchant_service)

        # Seed some transactions
        for i in range(6):
            tx = Transaction.create(
                user_id=self.user_id,
                posted_date=date(2026, 7, i + 1),
                merchant=f"Merchant {i}",
                description=f"Tx {i}",
                amount=Decimal(f"{(i + 1) * 100}.00"),
                direction=TransactionDirection.DEBIT,
                category="Shopping",
            )
            self.repository.save_transaction(tx)

    def test_dashboard_returns_summary(self) -> None:
        dashboard = self.analytics.dashboard(user_id=self.user_id, today=date(2026, 7, 17))
        self.assertIsNotNone(dashboard)
        self.assertIsNotNone(dashboard.summary)
        self.assertEqual(dashboard.summary.transaction_count, 6)

    def test_dashboard_cache_hit(self) -> None:
        """Same call twice should use cached result (same object)."""
        result1 = self.analytics.dashboard(user_id=self.user_id, today=date(2026, 7, 17))
        result2 = self.analytics.dashboard(user_id=self.user_id, today=date(2026, 7, 17))
        self.assertIs(result1, result2)  # Same object from cache

    def test_dashboard_cache_miss_after_new_transaction(self) -> None:
        """Adding a transaction should produce a new cache key and different result."""
        result1 = self.analytics.dashboard(user_id=self.user_id, today=date(2026, 7, 17))
        # Add a new transaction
        new_tx = Transaction.create(
            user_id=self.user_id,
            posted_date=date(2026, 7, 8),
            merchant="New Merchant",
            description="New Tx",
            amount=Decimal("9999.00"),
            direction=TransactionDirection.CREDIT,
        )
        self.repository.save_transaction(new_tx)
        result2 = self.analytics.dashboard(user_id=self.user_id, today=date(2026, 7, 17))
        self.assertIsNot(result1, result2)
        self.assertEqual(result2.summary.transaction_count, 7)

    def test_dashboard_top_n_constant(self) -> None:
        """TOP_N should be 5."""
        self.assertEqual(TOP_N, 5)

    def test_dashboard_top_categories_capped(self) -> None:
        dashboard = self.analytics.dashboard(user_id=self.user_id, today=date(2026, 7, 17))
        # top_categories should be at most TOP_N
        self.assertLessEqual(len(dashboard.top_categories), TOP_N)

    def test_dashboard_largest_expenses_capped(self) -> None:
        dashboard = self.analytics.dashboard(user_id=self.user_id, today=date(2026, 7, 17))
        self.assertLessEqual(len(dashboard.largest_expenses), TOP_N)


class TestAnalyticsDashboardIsolation(unittest.TestCase):
    """Verify that different users get isolated dashboards."""

    def setUp(self) -> None:
        self.user_a = uuid4()
        self.user_b = uuid4()
        self.repository = InMemoryFinanceRepository()
        merchant_service = MerchantService(self.repository, self.repository)
        self.analytics = AnalyticsService(self.repository, merchant_service)

        for user_id, merchant, amount in [
            (self.user_a, "Shop A", Decimal("500.00")),
            (self.user_b, "Shop B", Decimal("999.00")),
        ]:
            tx = Transaction.create(
                user_id=user_id,
                posted_date=date(2026, 7, 1),
                merchant=merchant,
                description=merchant,
                amount=amount,
                direction=TransactionDirection.DEBIT,
            )
            self.repository.save_transaction(tx)

    def test_dashboards_are_isolated_by_user(self) -> None:
        da = self.analytics.dashboard(user_id=self.user_a, today=date(2026, 7, 17))
        db = self.analytics.dashboard(user_id=self.user_b, today=date(2026, 7, 17))
        self.assertNotEqual(da.summary.total_expense, db.summary.total_expense)
        self.assertEqual(da.summary.total_expense, Decimal("500.00"))
        self.assertEqual(db.summary.total_expense, Decimal("999.00"))


if __name__ == "__main__":
    unittest.main()
