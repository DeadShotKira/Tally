"""AI Categorization Service - Suggests transaction categories.

Implements the categorization flow:
1. Check if rule matches → apply rule
2. Check merchant memory → apply memory
3. Query AI → get suggestion with confidence
4. Filter by confidence → auto-apply HIGH, require confirmation for MEDIUM/LOW
5. Fall back if AI unavailable
"""

from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from backend.app.features.intelligence.confidence_engine import ConfidenceEngine
from backend.app.features.intelligence.context_builder import AIContextBuilder
from backend.app.features.intelligence.merchant_memory import MerchantMemoryEngine
from backend.app.features.intelligence.models import AICategory, ConfidenceLevel
from backend.app.features.intelligence.providers import AIProvider, MockAIProvider
from backend.app.features.intelligence.rule_engine import RuleEngine
from backend.app.features.transactions.models import Transaction


logger = logging.getLogger(__name__)


class CategorizationResult:
    """Result of categorization attempt."""

    def __init__(
        self,
        category: str | None,
        confidence: float,
        confidence_level: ConfidenceLevel,
        source: str,  # "rule", "memory", "ai", "fallback"
        reasoning: str | None = None,
        auto_applied: bool = False,
    ):
        """Initialize categorization result.
        
        Args:
            category: Suggested category
            confidence: Confidence score (0.0-1.0)
            confidence_level: Confidence level
            source: Source of suggestion
            reasoning: Explanation for suggestion
            auto_applied: Whether to auto-apply
        """
        self.category = category
        self.confidence = confidence
        self.confidence_level = confidence_level
        self.source = source
        self.reasoning = reasoning
        self.auto_applied = auto_applied

    def requires_confirmation(self) -> bool:
        """Check if user confirmation is required."""
        return self.confidence_level != ConfidenceLevel.HIGH


class CategorizationService:
    """Service for categorizing transactions."""

    def __init__(
        self,
        rule_engine: RuleEngine | None = None,
        merchant_memory_engine: MerchantMemoryEngine | None = None,
        ai_provider: AIProvider | None = None,
        context_builder: AIContextBuilder | None = None,
        confidence_engine: ConfidenceEngine | None = None,
    ):
        """Initialize categorization service.
        
        Args:
            rule_engine: Optional custom rule engine
            merchant_memory_engine: Optional custom merchant memory engine
            ai_provider: Optional custom AI provider
            context_builder: Optional custom context builder
            confidence_engine: Optional custom confidence engine
        """
        self.rule_engine = rule_engine or RuleEngine()
        self.merchant_memory_engine = merchant_memory_engine or MerchantMemoryEngine()
        self.ai_provider = ai_provider or MockAIProvider()
        self.context_builder = context_builder or AIContextBuilder()
        self.confidence_engine = confidence_engine or ConfidenceEngine()
        self.logger = logging.getLogger(__name__)

    async def categorize(
        self,
        transaction: Transaction,
        user_id: UUID,
        rules: list[Any] | None = None,
        existing_categories: list[str] | None = None,
        allow_ai: bool = True,
        min_confidence: float = 0.0,
    ) -> CategorizationResult:
        """Categorize a transaction.
        
        Args:
            transaction: Transaction to categorize
            user_id: User ID
            rules: List of rules to evaluate
            existing_categories: Valid category list for context
            allow_ai: Whether to allow AI for suggestion
            min_confidence: Minimum confidence threshold
            
        Returns:
            CategorizationResult with category and confidence
        """
        self.logger.info(
            f"Categorizing transaction {transaction.id}: {transaction.merchant}"
        )

        # Step 1: Check rules
        if rules:
            rule_match = self.rule_engine.evaluate_rules(transaction, rules)
            if rule_match:
                category = rule_match.action.get("category")
                if category:
                    self.logger.info(f"Rule matched: {rule_match.rule_name}")
                    return CategorizationResult(
                        category=category,
                        confidence=1.0,
                        confidence_level=ConfidenceLevel.HIGH,
                        source="rule",
                        reasoning=f"Matched rule: {rule_match.rule_name}",
                        auto_applied=True,
                    )

        # Step 2: Check merchant memory
        _, memory_match = self.merchant_memory_engine.apply_memory_to_transaction(
            transaction, user_id
        )
        if memory_match and memory_match.category:
            self.logger.info(
                f"Merchant memory matched: {memory_match.canonical}"
            )
            return CategorizationResult(
                category=memory_match.category,
                confidence=0.95,
                confidence_level=ConfidenceLevel.HIGH,
                source="memory",
                reasoning=f"Learned from previous decision: {memory_match.canonical}",
                auto_applied=True,
            )

        # Step 3: Query AI if available
        if allow_ai and self.ai_provider.is_available():
            try:
                context = self.context_builder.build_categorization_context(
                    transaction, existing_categories
                )

                ai_suggestion = await self.ai_provider.categorize(
                    context, existing_categories or []
                )

                # Adjust confidence
                adjusted = self.confidence_engine.adjust_category_suggestion(
                    ai_suggestion
                )

                self.logger.info(
                    f"AI suggestion: {adjusted.category} "
                    f"(confidence: {adjusted.confidence:.2f})"
                )

                # Check if confidence meets minimum
                if adjusted.confidence < min_confidence:
                    self.logger.warning(
                        f"AI confidence {adjusted.confidence:.2f} "
                        f"below minimum {min_confidence}"
                    )
                    return self._fallback_categorization(transaction, existing_categories)

                auto_applied = self.confidence_engine.should_auto_apply(
                    adjusted.confidence, adjusted.confidence_level
                )

                return CategorizationResult(
                    category=adjusted.category,
                    confidence=adjusted.confidence,
                    confidence_level=adjusted.confidence_level,
                    source="ai",
                    reasoning=adjusted.reasoning,
                    auto_applied=auto_applied,
                )

            except Exception as e:
                self.logger.error(f"AI categorization failed: {e}")
                return self._fallback_categorization(transaction, existing_categories)

        # Step 4: Fallback
        return self._fallback_categorization(transaction, existing_categories)

    def _fallback_categorization(
        self,
        transaction: Transaction,
        existing_categories: list[str] | None = None,
    ) -> CategorizationResult:
        """Fallback categorization when AI is unavailable.
        
        Args:
            transaction: Transaction to categorize
            existing_categories: Valid categories
            
        Returns:
            Low-confidence categorization result
        """
        # If transaction has a category, keep it
        if transaction.category:
            return CategorizationResult(
                category=transaction.category,
                confidence=0.0,
                confidence_level=ConfidenceLevel.LOW,
                source="fallback",
                reasoning="Kept existing category (AI unavailable)",
                auto_applied=False,
            )

        # Otherwise suggest first available category
        if existing_categories:
            return CategorizationResult(
                category=existing_categories[0],
                confidence=0.0,
                confidence_level=ConfidenceLevel.LOW,
                source="fallback",
                reasoning="Default category (AI unavailable)",
                auto_applied=False,
            )

        # No category available
        return CategorizationResult(
            category=None,
            confidence=0.0,
            confidence_level=ConfidenceLevel.LOW,
            source="fallback",
            reasoning="No categorization available",
            auto_applied=False,
        )


class BatchCategorizationService:
    """Service for batch categorizing multiple transactions."""

    def __init__(self, categorization_service: CategorizationService | None = None):
        """Initialize batch service.
        
        Args:
            categorization_service: Optional custom categorization service
        """
        self.service = categorization_service or CategorizationService()

    async def categorize_batch(
        self,
        transactions: list[Transaction],
        user_id: UUID,
        rules: list[Any] | None = None,
        existing_categories: list[str] | None = None,
    ) -> list[CategorizationResult]:
        """Categorize multiple transactions.
        
        Args:
            transactions: Transactions to categorize
            user_id: User ID
            rules: Rules to apply
            existing_categories: Valid categories
            
        Returns:
            List of categorization results
        """
        results = []
        for transaction in transactions:
            result = await self.service.categorize(
                transaction=transaction,
                user_id=user_id,
                rules=rules,
                existing_categories=existing_categories,
            )
            results.append(result)

        return results
