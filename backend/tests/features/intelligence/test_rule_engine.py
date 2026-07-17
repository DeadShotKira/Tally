"""Tests for Rule Engine."""

import pytest
from decimal import Decimal
from datetime import date
from uuid import uuid4

from backend.app.features.intelligence.rule_engine import (
    RuleEngine,
    RuleEvaluator,
    RuleType,
)
from backend.app.features.intelligence.models import Rule
from backend.app.features.imports.models import TransactionDirection
from backend.app.features.transactions.models import Transaction


class TestRuleEvaluator:
    """Test rule evaluation logic."""

    def test_merchant_exact_match(self):
        """Test exact merchant matching."""
        txn = Transaction.create(
            user_id=uuid4(),
            posted_date=date.today(),
            amount=Decimal("100"),
            direction=TransactionDirection.DEBIT,
            merchant="Amazon",
        )

        rule = Rule.build_exact_match_rule(
            user_id=uuid4(),
            merchant="Amazon",
            category="Shopping",
        )

        evaluator = RuleEvaluator()
        assert evaluator.evaluate(rule, txn)

    def test_merchant_exact_case_insensitive(self):
        """Test exact match is case-insensitive."""
        txn = Transaction.create(
            user_id=uuid4(),
            posted_date=date.today(),
            amount=Decimal("100"),
            direction=TransactionDirection.DEBIT,
            merchant="amazon",
        )

        rule = Rule.build_exact_match_rule(
            user_id=uuid4(),
            merchant="Amazon",
            category="Shopping",
        )

        evaluator = RuleEvaluator()
        assert evaluator.evaluate(rule, txn)

    def test_merchant_contains_match(self):
        """Test contains pattern matching."""
        txn = Transaction.create(
            user_id=uuid4(),
            posted_date=date.today(),
            amount=Decimal("500"),
            direction=TransactionDirection.DEBIT,
            merchant="Swiggy Order #123",
        )

        rule = Rule.build_pattern_rule(
            user_id=uuid4(),
            pattern_type=RuleType.MERCHANT_CONTAINS,
            pattern="Swiggy",
            category="Food",
        )

        evaluator = RuleEvaluator()
        assert evaluator.evaluate(rule, txn)

    def test_merchant_prefix_match(self):
        """Test prefix matching."""
        txn = Transaction.create(
            user_id=uuid4(),
            posted_date=date.today(),
            amount=Decimal("1000"),
            direction=TransactionDirection.DEBIT,
            merchant="SALARY-COMPANY INC",
        )

        rule = Rule.build_pattern_rule(
            user_id=uuid4(),
            pattern_type=RuleType.MERCHANT_PREFIX,
            pattern="SALARY",
            category="Income",
        )

        evaluator = RuleEvaluator()
        assert evaluator.evaluate(rule, txn)

    def test_amount_threshold_match(self):
        """Test amount threshold matching."""
        txn = Transaction.create(
            user_id=uuid4(),
            posted_date=date.today(),
            amount=Decimal("5000"),
            direction=TransactionDirection.DEBIT,
            merchant="Store",
        )

        from backend.app.features.intelligence.models import Rule as RuleModel
        from datetime import UTC, datetime

        rule = RuleModel(
            id=uuid4(),
            user_id=uuid4(),
            name="Large expense",
            description=None,
            rule_type=RuleType.AMOUNT_THRESHOLD.value,
            priority=100,
            conditions={"amount": 1000, "operator": ">="},
            action={"tags": ["large_expense"]},
            enabled=True,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        evaluator = RuleEvaluator()
        assert evaluator.evaluate(rule, txn)

    def test_no_match_returns_false(self):
        """Test that non-matching rule returns false."""
        txn = Transaction.create(
            user_id=uuid4(),
            posted_date=date.today(),
            amount=Decimal("100"),
            direction=TransactionDirection.DEBIT,
            merchant="Store A",
        )

        rule = Rule.build_exact_match_rule(
            user_id=uuid4(),
            merchant="Store B",
            category="Shopping",
        )

        evaluator = RuleEvaluator()
        assert not evaluator.evaluate(rule, txn)


class TestRuleEngine:
    """Test rule engine."""

    def test_evaluate_single_matching_rule(self):
        """Test evaluating matching rule."""
        txn = Transaction.create(
            user_id=uuid4(),
            posted_date=date.today(),
            amount=Decimal("500"),
            direction=TransactionDirection.DEBIT,
            merchant="Amazon",
        )

        rule = Rule.build_exact_match_rule(
            user_id=uuid4(),
            merchant="Amazon",
            category="Shopping",
        )

        engine = RuleEngine()
        match = engine.evaluate_rules(txn, [rule])

        assert match is not None
        assert match.matched
        assert match.action["category"] == "Shopping"

    def test_priority_order(self):
        """Test that rules are evaluated in priority order."""
        txn = Transaction.create(
            user_id=uuid4(),
            posted_date=date.today(),
            amount=Decimal("500"),
            direction=TransactionDirection.DEBIT,
            merchant="Amazon Prime",
        )

        # Two rules that could match, different priorities
        from backend.app.features.intelligence.models import Rule as RuleModel
        from datetime import UTC, datetime

        rule1 = RuleModel(
            id=uuid4(),
            user_id=uuid4(),
            name="Amazon",
            description=None,
            rule_type=RuleType.MERCHANT_EXACT.value,
            priority=100,
            conditions={"merchant": "Amazon"},
            action={"category": "Shopping"},
            enabled=True,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        rule2 = RuleModel(
            id=uuid4(),
            user_id=uuid4(),
            name="Prime",
            description=None,
            rule_type=RuleType.MERCHANT_CONTAINS.value,
            priority=50,  # Higher priority
            conditions={"merchant": "Prime"},
            action={"category": "Subscriptions"},
            enabled=True,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        engine = RuleEngine()
        match = engine.evaluate_rules(txn, [rule1, rule2])

        # Should match rule2 (Prime) because it has higher priority (lower number)
        assert match.action["category"] == "Subscriptions"

    def test_no_matching_rule(self):
        """Test when no rules match."""
        txn = Transaction.create(
            user_id=uuid4(),
            posted_date=date.today(),
            amount=Decimal("100"),
            direction=TransactionDirection.DEBIT,
            merchant="Unknown Store",
        )

        rule = Rule.build_exact_match_rule(
            user_id=uuid4(),
            merchant="Known Store",
            category="Shopping",
        )

        engine = RuleEngine()
        match = engine.evaluate_rules(txn, [rule])

        assert match is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
