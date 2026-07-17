"""Rule Engine for deterministic transaction categorization and merchant resolution.

Rules execute before AI and allow users to define patterns that automatically
apply categories, rename merchants, or flag transactions.

Rule types:
- merchant_exact: Exact merchant name match
- merchant_contains: Merchant contains substring (case-insensitive)
- merchant_prefix: Merchant starts with prefix
- merchant_suffix: Merchant ends with suffix
- merchant_regex: Regular expression matching
- amount_threshold: Amount exceeds threshold
- combined: Multiple conditions (AND logic)

Rules are evaluated by priority (lower = higher priority).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from backend.app.features.intelligence.models import Rule
from backend.app.features.transactions.models import Transaction


class RuleType(str, Enum):
    """Types of rules supported."""
    MERCHANT_EXACT = "merchant_exact"
    MERCHANT_CONTAINS = "merchant_contains"
    MERCHANT_PREFIX = "merchant_prefix"
    MERCHANT_SUFFIX = "merchant_suffix"
    MERCHANT_REGEX = "merchant_regex"
    AMOUNT_THRESHOLD = "amount_threshold"
    COMBINED = "combined"


@dataclass(frozen=True)
class RuleMatch:
    """Result of rule matching."""
    matched: bool
    rule_id: UUID
    rule_name: str
    priority: int
    action: dict[str, Any]


class RuleEvaluator:
    """Evaluates rules against transactions."""

    @staticmethod
    def _match_merchant_exact(
        rule: Rule,
        transaction: Transaction,
    ) -> bool:
        """Check if merchant matches exactly."""
        pattern = rule.conditions.get("merchant", "").lower()
        merchant = transaction.merchant.lower()
        return merchant == pattern

    @staticmethod
    def _match_merchant_contains(
        rule: Rule,
        transaction: Transaction,
    ) -> bool:
        """Check if merchant contains substring."""
        pattern = rule.conditions.get("merchant", "").lower()
        merchant = transaction.merchant.lower()
        return pattern in merchant

    @staticmethod
    def _match_merchant_prefix(
        rule: Rule,
        transaction: Transaction,
    ) -> bool:
        """Check if merchant starts with prefix."""
        pattern = rule.conditions.get("merchant", "").lower()
        merchant = transaction.merchant.lower()
        return merchant.startswith(pattern)

    @staticmethod
    def _match_merchant_suffix(
        rule: Rule,
        transaction: Transaction,
    ) -> bool:
        """Check if merchant ends with suffix."""
        pattern = rule.conditions.get("merchant", "").lower()
        merchant = transaction.merchant.lower()
        return merchant.endswith(pattern)

    @staticmethod
    def _match_merchant_regex(
        rule: Rule,
        transaction: Transaction,
    ) -> bool:
        """Check if merchant matches regex pattern."""
        pattern = rule.conditions.get("merchant", "")
        merchant = transaction.merchant
        try:
            return re.search(pattern, merchant, re.IGNORECASE) is not None
        except re.error:
            return False

    @staticmethod
    def _match_amount_threshold(
        rule: Rule,
        transaction: Transaction,
    ) -> bool:
        """Check if amount exceeds threshold."""
        threshold = Decimal(str(rule.conditions.get("amount", 0)))
        operator = rule.conditions.get("operator", ">=")

        if operator == ">=":
            return transaction.amount >= threshold
        elif operator == ">":
            return transaction.amount > threshold
        elif operator == "<=":
            return transaction.amount <= threshold
        elif operator == "<":
            return transaction.amount < threshold
        elif operator == "==":
            return transaction.amount == threshold

        return False

    @staticmethod
    def _match_combined(
        rule: Rule,
        transaction: Transaction,
    ) -> bool:
        """Check if all conditions match (AND logic)."""
        conditions = rule.conditions.get("conditions", [])
        evaluator = RuleEvaluator()

        for condition in conditions:
            # Each condition has type and its own conditions
            condition_type = condition.get("type")
            test_rule = Rule(
                id=rule.id,
                user_id=rule.user_id,
                name=rule.name,
                description=None,
                rule_type=condition_type,
                priority=rule.priority,
                conditions=condition.get("conditions", {}),
                action=rule.action,
            )

            if not evaluator.evaluate(test_rule, transaction).matched:
                return False

        return True

    def evaluate(
        self,
        rule: Rule,
        transaction: Transaction,
    ) -> bool:
        """Evaluate if rule matches transaction.
        
        Args:
            rule: Rule to evaluate
            transaction: Transaction to test
            
        Returns:
            True if rule matches, False otherwise
        """
        if not rule.enabled:
            return False

        rule_type = RuleType(rule.rule_type)

        if rule_type == RuleType.MERCHANT_EXACT:
            return self._match_merchant_exact(rule, transaction)
        elif rule_type == RuleType.MERCHANT_CONTAINS:
            return self._match_merchant_contains(rule, transaction)
        elif rule_type == RuleType.MERCHANT_PREFIX:
            return self._match_merchant_prefix(rule, transaction)
        elif rule_type == RuleType.MERCHANT_SUFFIX:
            return self._match_merchant_suffix(rule, transaction)
        elif rule_type == RuleType.MERCHANT_REGEX:
            return self._match_merchant_regex(rule, transaction)
        elif rule_type == RuleType.AMOUNT_THRESHOLD:
            return self._match_amount_threshold(rule, transaction)
        elif rule_type == RuleType.COMBINED:
            return self._match_combined(rule, transaction)

        # Unsupported or unknown rule types fall through and return False
        return False


class RuleEngine:
    """Deterministic rule engine for transaction processing.
    
    Rules are evaluated in priority order (lower priority value = higher priority).
    First matching rule wins.
    """

    def __init__(self):
        """Initialize rule engine."""
        self.evaluator = RuleEvaluator()

    def evaluate_rules(
        self,
        transaction: Transaction,
        rules: list[Rule],
    ) -> RuleMatch | None:
        """Find first matching rule for transaction.
        
        Args:
            transaction: Transaction to evaluate
            rules: List of rules to test
            
        Returns:
            RuleMatch if a rule matches, None otherwise
        """
        # Sort by priority (lower = higher priority)
        sorted_rules = sorted(rules, key=lambda r: r.priority)

        for rule in sorted_rules:
            if self.evaluator.evaluate(rule, transaction):
                return RuleMatch(
                    matched=True,
                    rule_id=rule.id,
                    rule_name=rule.name,
                    priority=rule.priority,
                    action=rule.action,
                )

        return None

    def apply_rule_action(
        self,
        transaction: Transaction,
        rule_match: RuleMatch,
    ) -> Transaction:
        """Apply matched rule's action to transaction.
        
        Args:
            transaction: Original transaction
            rule_match: Matched rule with action
            
        Returns:
            Modified transaction
        """
        action = rule_match.action
        category = action.get("category", transaction.category)
        merchant = action.get("merchant", transaction.merchant)
        tags = tuple(action.get("tags", transaction.tags))

        # Create new transaction with updated fields
        # In a real implementation, this would update the database
        return Transaction.create(
            user_id=transaction.user_id,
            posted_date=transaction.posted_date,
            amount=transaction.amount,
            direction=transaction.direction,
            merchant=merchant,
            description=transaction.description,
            category=category,
            tags=tags,
            notes=transaction.notes,
            import_id=transaction.import_id,
            balance=transaction.balance,
            reference_number=transaction.reference_number,
        )

    @staticmethod
    def build_exact_match_rule(
        user_id: UUID,
        merchant: str,
        category: str | None = None,
        priority: int = 100,
    ) -> Rule:
        """Build a simple exact merchant match rule.
        
        Args:
            user_id: User ID
            merchant: Exact merchant name to match
            category: Category to assign
            priority: Rule priority
            
        Returns:
            Rule instance
        """
        return Rule(
            id=uuid4(),
            user_id=user_id,
            name=f"Exact: {merchant}",
            description=None,
            rule_type=RuleType.MERCHANT_EXACT.value,
            priority=priority,
            conditions={"merchant": merchant},
            action={"category": category} if category else {},
            enabled=True,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

    @staticmethod
    def build_pattern_rule(
        user_id: UUID,
        pattern_type: RuleType,
        pattern: str,
        category: str | None = None,
        priority: int = 100,
    ) -> Rule:
        """Build a pattern matching rule.
        
        Args:
            user_id: User ID
            pattern_type: Type of pattern matching
            pattern: Pattern to match
            category: Category to assign
            priority: Rule priority
            
        Returns:
            Rule instance
        """
        return Rule(
            id=uuid4(),
            user_id=user_id,
            name=f"{pattern_type.value}: {pattern}",
            description=None,
            rule_type=pattern_type.value,
            priority=priority,
            conditions={"merchant": pattern},
            action={"category": category} if category else {},
            enabled=True,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
