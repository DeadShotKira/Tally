"""Recurring Transaction Detection and Insights Engine.

Detects recurring payments, subscriptions, and generates proactive financial insights.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from backend.app.features.intelligence.models import (
    Insight,
    RecurringTransaction,
)
from backend.app.features.transactions.models import Transaction


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RecurringPattern:
    """A detected recurring pattern."""
    merchant: str
    category: str | None
    amount: Decimal
    occurrence_dates: list[str]  # ISO format dates
    frequency_days: list[int]  # Days between occurrences
    average_days: float
    confidence: float  # 0.0-1.0
    transaction_count: int


class RecurringDetector:
    """Detects recurring payments and subscriptions."""

    def __init__(self, min_occurrences: int = 3, max_days_variance: int = 5):
        """Initialize recurring detector.
        
        Args:
            min_occurrences: Minimum transactions to consider recurring
            max_days_variance: Maximum variance in days between occurrences
        """
        self.min_occurrences = min_occurrences
        self.max_days_variance = max_days_variance

    def detect_recurring(
        self,
        transactions: list[Transaction],
        user_id: UUID,
    ) -> list[RecurringTransaction]:
        """Detect recurring transactions.
        
        Args:
            transactions: List of transactions to analyze
            user_id: User ID
            
        Returns:
            List of detected recurring transactions
        """
        # Group by merchant and approximate amount
        patterns = self._find_patterns(transactions)
        recurring = []

        for merchant, patterns_list in patterns.items():
            for pattern in patterns_list:
                if len(pattern.occurrence_dates) >= self.min_occurrences:
                    # Create recurring transaction record
                    recurring_txn = RecurringTransaction(
                        id=uuid4(),
                        user_id=user_id,
                        merchant=pattern.merchant,
                        category=pattern.category,
                        amount=pattern.amount,
                        average_days_between=int(pattern.average_days),
                        last_occurrence_date=pattern.occurrence_dates[-1],
                        transaction_count=len(pattern.occurrence_dates),
                        confidence=pattern.confidence,
                    )
                    recurring.append(recurring_txn)

        return recurring

    def _find_patterns(
        self,
        transactions: list[Transaction],
    ) -> dict[str, list[RecurringPattern]]:
        """Find recurring patterns in transactions.
        
        Args:
            transactions: Transactions to analyze
            
        Returns:
            Dictionary mapping merchants to patterns
        """
        # Group by merchant
        by_merchant: dict[str, list[Transaction]] = defaultdict(list)
        for txn in transactions:
            by_merchant[txn.merchant.lower()].append(txn)

        patterns: dict[str, list[RecurringPattern]] = defaultdict(list)

        for merchant, txns in by_merchant.items():
            if len(txns) < self.min_occurrences:
                continue

            # Sort by date
            sorted_txns = sorted(txns, key=lambda t: t.posted_date)

            # Group by amount (allow some variance)
            amount_groups = self._group_by_amount(sorted_txns)

            for amount, txns_with_amount in amount_groups.items():
                if len(txns_with_amount) < self.min_occurrences:
                    continue

                # Calculate frequency
                dates = [t.posted_date.isoformat() for t in txns_with_amount]
                frequencies = self._calculate_frequencies(
                    [t.posted_date for t in txns_with_amount]
                )

                if not frequencies:
                    continue

                avg_days = sum(frequencies) / len(frequencies)
                variance = self._calculate_variance(frequencies, avg_days)

                # Check if frequency is consistent
                if variance <= self.max_days_variance:
                    confidence = self._calculate_pattern_confidence(
                        len(frequencies), variance
                    )

                    pattern = RecurringPattern(
                        merchant=merchant,
                        category=txns_with_amount[0].category,
                        amount=amount,
                        occurrence_dates=dates,
                        frequency_days=frequencies,
                        average_days=avg_days,
                        confidence=confidence,
                        transaction_count=len(txns_with_amount),
                    )
                    patterns[merchant].append(pattern)

        return patterns

    def _group_by_amount(
        self,
        transactions: list[Transaction],
    ) -> dict[Decimal, list[Transaction]]:
        """Group transactions by amount with tolerance.
        
        Args:
            transactions: Transactions to group
            
        Returns:
            Dictionary mapping amounts to transactions
        """
        groups: dict[Decimal, list[Transaction]] = defaultdict(list)

        for txn in transactions:
            # Find group this belongs to (±1%)
            found_group = None
            for existing_amount in groups:
                pct_diff = abs(
                    (txn.amount - existing_amount) / existing_amount * 100
                )
                if pct_diff <= 1.0:
                    found_group = existing_amount
                    break

            if found_group:
                groups[found_group].append(txn)
            else:
                groups[txn.amount].append(txn)

        return groups

    @staticmethod
    def _calculate_frequencies(dates: list[date]) -> list[int]:
        """Calculate days between consecutive dates.
        
        Args:
            dates: List of dates
            
        Returns:
            List of day differences
        """
        if len(dates) < 2:
            return []

        frequencies = []
        sorted_dates = sorted(dates)

        for i in range(1, len(sorted_dates)):
            delta = (sorted_dates[i] - sorted_dates[i - 1]).days
            frequencies.append(delta)

        return frequencies

    @staticmethod
    def _calculate_variance(frequencies: list[int], mean: float) -> float:
        """Calculate variance in frequencies.
        
        Args:
            frequencies: List of frequencies
            mean: Mean frequency
            
        Returns:
            Standard deviation
        """
        if len(frequencies) <= 1:
            return 0.0

        variance = sum((f - mean) ** 2 for f in frequencies) / len(frequencies)
        return variance ** 0.5

    @staticmethod
    def _calculate_pattern_confidence(
        occurrences: int,
        variance: float,
    ) -> float:
        """Calculate confidence in recurring pattern.
        
        Args:
            occurrences: Number of occurrences
            variance: Variance in frequency
            
        Returns:
            Confidence score (0.0-1.0)
        """
        # More occurrences = higher confidence
        occurrence_score = min(1.0, occurrences / 12.0)

        # Lower variance = higher confidence
        variance_score = max(0.0, 1.0 - (variance / 10.0))

        return (occurrence_score * 0.7) + (variance_score * 0.3)


class InsightsEngine:
    """Generates proactive financial insights."""

    def __init__(self, recurring_detector: RecurringDetector | None = None):
        """Initialize insights engine.
        
        Args:
            recurring_detector: Optional custom recurring detector
        """
        self.recurring_detector = recurring_detector or RecurringDetector()
        self.logger = logging.getLogger(__name__)

    def generate_insights(
        self,
        transactions: list[Transaction],
        user_id: UUID,
        lookback_days: int = 90,
    ) -> list[Insight]:
        """Generate insights for a user.
        
        Args:
            transactions: Recent transactions
            user_id: User ID
            lookback_days: Days of history to analyze
            
        Returns:
            List of generated insights
        """
        insights: list[Insight] = []

        # Detect recurring transactions
        recurring = self.recurring_detector.detect_recurring(transactions, user_id)
        for r in recurring:
            if r.transaction_count >= 3:  # Only if confirmed recurring
                insight = Insight(
                    id=uuid4(),
                    user_id=user_id,
                    insight_type="subscription_detected",
                    title=f"Recurring: {r.merchant}",
                    description=(
                        f"You have a recurring charge of ₹{r.amount} every "
                        f"~{r.average_days_between} days from {r.merchant}."
                    ),
                    severity="info",
                    related_metric="subscriptions",
                    metadata={
                        "merchant": r.merchant,
                        "amount": str(r.amount),
                        "frequency_days": str(int(r.average_days_between)),
                    },
                )
                insights.append(insight)

        # Spending anomaly detection
        anomalies = self._detect_spending_anomalies(transactions)
        insights.extend(anomalies)

        # Trend analysis
        trends = self._analyze_trends(transactions)
        insights.extend(trends)

        # Category-specific insights
        category_insights = self._analyze_categories(transactions)
        insights.extend(category_insights)

        return insights

    def _detect_spending_anomalies(
        self,
        transactions: list[Transaction],
    ) -> list[Insight]:
        """Detect unusual spending patterns.
        
        Args:
            transactions: Transactions to analyze
            
        Returns:
            List of anomaly insights
        """
        insights: list[Insight] = []

        if not transactions:
            return insights

        # Find unusually large expenses
        amounts = [t.amount for t in transactions if t.direction.value == "debit"]
        if not amounts:
            return insights

        avg_amount = sum(amounts) / len(amounts)
        threshold = avg_amount * 2.5

        large_expenses = [
            t for t in transactions
            if t.direction.value == "debit" and t.amount > threshold
        ]

        for expense in large_expenses[:3]:  # Show top 3
            insight = Insight(
                id=uuid4(),
                user_id=transactions[0].user_id,
                insight_type="anomaly",
                title="Unusual expense detected",
                description=(
                    f"You spent ₹{expense.amount} at {expense.merchant}, "
                    f"which is significantly higher than your average."
                ),
                severity="warning",
                related_metric="anomalies",
                metadata={
                    "merchant": expense.merchant,
                    "amount": str(expense.amount),
                    "date": expense.posted_date.isoformat(),
                },
            )
            insights.append(insight)

        return insights

    def _analyze_trends(
        self,
        transactions: list[Transaction],
    ) -> list[Insight]:
        """Analyze spending trends.
        
        Args:
            transactions: Transactions to analyze
            
        Returns:
            List of trend insights
        """
        insights: list[Insight] = []

        if len(transactions) < 30:
            return insights

        # Compare last 14 days to previous 14 days
        today = date.today()
        two_weeks_ago = today - timedelta(days=14)
        four_weeks_ago = today - timedelta(days=28)

        current_spend = sum(
            t.amount
            for t in transactions
            if two_weeks_ago <= t.posted_date <= today
            and t.direction.value == "debit"
        )

        previous_spend = sum(
            t.amount
            for t in transactions
            if four_weeks_ago <= t.posted_date < two_weeks_ago
            and t.direction.value == "debit"
        )

        if previous_spend > 0:
            pct_change = ((current_spend - previous_spend) / previous_spend) * 100

            if abs(pct_change) > 20:
                direction = "increased" if pct_change > 0 else "decreased"
                severity = "warning" if pct_change > 0 else "info"

                insight = Insight(
                    id=uuid4(),
                    user_id=transactions[0].user_id,
                    insight_type="spending_trend",
                    title=f"Spending {direction}",
                    description=(
                        f"Your spending has {direction} by {abs(pct_change):.1f}% "
                        f"compared to two weeks ago."
                    ),
                    severity=severity,
                    related_metric="trends",
                    metadata={
                        "direction": direction,
                        "percentage_change": f"{pct_change:.1f}",
                        "current_period": str(current_spend),
                        "previous_period": str(previous_spend),
                    },
                )
                insights.append(insight)

        return insights

    def _analyze_categories(
        self,
        transactions: list[Transaction],
    ) -> list[Insight]:
        """Analyze spending by category.
        
        Args:
            transactions: Transactions to analyze
            
        Returns:
            List of category insights
        """
        insights: list[Insight] = []

        # Categorize spending
        by_category: dict[str, Decimal] = defaultdict(Decimal)
        for t in transactions:
            if t.direction.value == "debit" and t.category:
                by_category[t.category] += t.amount

        total_spend = sum(by_category.values())
        if total_spend == 0:
            return insights

        # Find category with highest spending
        if by_category:
            top_category = max(by_category.items(), key=lambda x: x[1])
            pct_of_total = (top_category[1] / total_spend) * 100

            insight = Insight(
                id=uuid4(),
                user_id=transactions[0].user_id,
                insight_type="category_insight",
                title=f"Top spending: {top_category[0]}",
                description=(
                    f"{top_category[0]} accounts for {pct_of_total:.1f}% "
                    f"of your total spending."
                ),
                severity="info",
                related_metric="categories",
                metadata={
                    "category": top_category[0],
                    "amount": str(top_category[1]),
                    "percentage": f"{pct_of_total:.1f}",
                },
            )
            insights.append(insight)

        return insights
