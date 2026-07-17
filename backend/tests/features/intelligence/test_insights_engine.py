"""Unit tests for the InsightsEngine and RecurringDetector."""

import unittest
from datetime import date
from decimal import Decimal
from uuid import uuid4

from backend.app.features.imports.models import TransactionDirection
from backend.app.features.intelligence.insights_engine import InsightsEngine, RecurringDetector
from backend.app.features.transactions.models import Transaction


def _make_tx(
    *,
    user_id,
    posted_date: date,
    merchant: str,
    amount: Decimal,
    direction: TransactionDirection = TransactionDirection.DEBIT,
    category: str | None = None,
) -> Transaction:
    return Transaction.create(
        user_id=user_id,
        posted_date=posted_date,
        merchant=merchant,
        description=merchant,
        amount=amount,
        direction=direction,
        category=category,
    )


class TestRecurringDetector(unittest.TestCase):
    def setUp(self) -> None:
        self.user_id = uuid4()
        self.detector = RecurringDetector(min_occurrences=3, max_days_variance=5)

    def test_detects_monthly_recurring(self) -> None:
        # Monthly subscription: ~30 days apart
        transactions = [
            _make_tx(user_id=self.user_id, posted_date=date(2026, 1, 1), merchant="Netflix", amount=Decimal("649.00")),
            _make_tx(user_id=self.user_id, posted_date=date(2026, 2, 1), merchant="Netflix", amount=Decimal("649.00")),
            _make_tx(user_id=self.user_id, posted_date=date(2026, 3, 1), merchant="Netflix", amount=Decimal("649.00")),
            _make_tx(user_id=self.user_id, posted_date=date(2026, 4, 1), merchant="Netflix", amount=Decimal("649.00")),
        ]
        results = self.detector.detect_recurring(transactions, self.user_id)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].merchant, "netflix")  # lowercased
        self.assertEqual(results[0].transaction_count, 4)
        self.assertGreater(results[0].confidence, 0.0)

    def test_does_not_detect_irregular_payments(self) -> None:
        # Irregular intervals: 5, 15, 40 days
        transactions = [
            _make_tx(user_id=self.user_id, posted_date=date(2026, 1, 1), merchant="Random Shop", amount=Decimal("200.00")),
            _make_tx(user_id=self.user_id, posted_date=date(2026, 1, 6), merchant="Random Shop", amount=Decimal("200.00")),
            _make_tx(user_id=self.user_id, posted_date=date(2026, 1, 21), merchant="Random Shop", amount=Decimal("200.00")),
            _make_tx(user_id=self.user_id, posted_date=date(2026, 3, 2), merchant="Random Shop", amount=Decimal("200.00")),
        ]
        results = self.detector.detect_recurring(transactions, self.user_id)
        self.assertEqual(len(results), 0)

    def test_no_recurring_with_single_transaction(self) -> None:
        transactions = [
            _make_tx(user_id=self.user_id, posted_date=date(2026, 1, 1), merchant="Once", amount=Decimal("100.00")),
        ]
        results = self.detector.detect_recurring(transactions, self.user_id)
        self.assertEqual(len(results), 0)

    def test_no_recurring_with_empty_list(self) -> None:
        results = self.detector.detect_recurring([], self.user_id)
        self.assertEqual(len(results), 0)


class TestInsightsEngine(unittest.TestCase):
    def setUp(self) -> None:
        self.user_id = uuid4()
        self.engine = InsightsEngine()

    def test_generates_subscription_insight_for_recurring(self) -> None:
        transactions = [
            _make_tx(user_id=self.user_id, posted_date=date(2026, 1, 1), merchant="Spotify", amount=Decimal("199.00")),
            _make_tx(user_id=self.user_id, posted_date=date(2026, 2, 1), merchant="Spotify", amount=Decimal("199.00")),
            _make_tx(user_id=self.user_id, posted_date=date(2026, 3, 1), merchant="Spotify", amount=Decimal("199.00")),
            _make_tx(user_id=self.user_id, posted_date=date(2026, 4, 1), merchant="Spotify", amount=Decimal("199.00")),
        ]
        insights = self.engine.generate_insights(transactions, self.user_id)
        subscription_insights = [i for i in insights if i.insight_type == "subscription_detected"]
        self.assertGreater(len(subscription_insights), 0)

    def test_detects_spending_anomaly(self) -> None:
        # Normal spending with one large outlier
        transactions = [
            _make_tx(user_id=self.user_id, posted_date=date(2026, 7, 1), merchant="Coffee", amount=Decimal("100.00")),
            _make_tx(user_id=self.user_id, posted_date=date(2026, 7, 2), merchant="Coffee", amount=Decimal("100.00")),
            _make_tx(user_id=self.user_id, posted_date=date(2026, 7, 3), merchant="Coffee", amount=Decimal("100.00")),
            _make_tx(user_id=self.user_id, posted_date=date(2026, 7, 4), merchant="Big Purchase", amount=Decimal("50000.00")),
        ]
        insights = self.engine.generate_insights(transactions, self.user_id)
        anomaly_insights = [i for i in insights if i.insight_type == "anomaly"]
        self.assertGreater(len(anomaly_insights), 0)

    def test_no_insights_for_empty_transactions(self) -> None:
        insights = self.engine.generate_insights([], self.user_id)
        self.assertEqual(insights, [])

    def test_insight_has_required_fields(self) -> None:
        transactions = [
            _make_tx(user_id=self.user_id, posted_date=date(2026, 7, 1), merchant="BIG PURCHASE", amount=Decimal("100000.00")),
            _make_tx(user_id=self.user_id, posted_date=date(2026, 7, 2), merchant="Coffee", amount=Decimal("100.00")),
            _make_tx(user_id=self.user_id, posted_date=date(2026, 7, 3), merchant="Coffee", amount=Decimal("100.00")),
        ]
        insights = self.engine.generate_insights(transactions, self.user_id)
        for insight in insights:
            self.assertIsNotNone(insight.id)
            self.assertEqual(insight.user_id, self.user_id)
            self.assertIsNotNone(insight.insight_type)
            self.assertIsNotNone(insight.title)


if __name__ == "__main__":
    unittest.main()
