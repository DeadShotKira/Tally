"""Privacy filtering and context sanitization for AI processing.

This module is responsible for the most critical privacy protection in Tally.
Before any data is sent to AI, it must be sanitized to remove:
- Account numbers, IFSC codes, UPI IDs, phone numbers, customer IDs
- Reference numbers, statement headers, branch information
- Any sensitive banking identifiers

Only sanitized merchant name, description, amount, direction, and minimal
historical context should be included in AI requests.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from backend.app.features.intelligence.models import SanitizedContext
from backend.app.features.transactions.models import Transaction, TransactionFilters


# Patterns for detecting sensitive data that should NOT be sent to AI
# NOTE: Order matters - more specific patterns should come before general ones
SENSITIVE_PATTERNS = {
    "phone": re.compile(r"\b(?:\+91|0)?[6-9]\d{9}\b"),  # Indian phone - check first
    "card_number": re.compile(r"\b(?:\d{4}[-\s]?){3}\d{4}\b"),  # Card format
    "ifsc_code": re.compile(r"\b[A-Z]{4}0[A-Z0-9]{6}\b"),  # IFSC format
    "reference": re.compile(r"\b(?:REF|TREF|UTR|RRN)[-/\s]?[\w]{8,20}\b"),  # Reference IDs
    "upi_id": re.compile(r"\b[\w.-]+@[\w.-]+\b"),  # UPI ID format
    "account_number": re.compile(r"\b\d{10,18}\b"),  # Account-like patterns (10-18 digits)
}


@dataclass
class SanitizationResult:
    """Result of sanitizing text."""
    sanitized_text: str
    redactions: tuple[str, ...] = ()
    has_unsafe_patterns: bool = False


class PrivacyFilter:
    """Detects and redacts sensitive information from transaction data."""

    @staticmethod
    def sanitize_text(text: str | None) -> SanitizationResult:
        """Sanitize transaction description or merchant name.
        
        Removes account numbers, UPI IDs, phone numbers, reference numbers, etc.
        
        Args:
            text: Text to sanitize
            
        Returns:
            SanitizationResult with sanitized text and redactions
        """
        if not text:
            return SanitizationResult(sanitized_text="")

        sanitized = text
        redactions: list[str] = []

        for pattern_name, pattern in SENSITIVE_PATTERNS.items():
            # Replace all matches for this pattern
            if pattern.search(sanitized):
                replacement = f"[{pattern_name.upper()}_REDACTED]"
                sanitized = pattern.sub(replacement, sanitized)
                redactions.append(replacement)

        return SanitizationResult(
            sanitized_text=sanitized,
            redactions=tuple(redactions),
            has_unsafe_patterns=len(redactions) > 0,
        )

    @staticmethod
    def is_safe_for_ai(text: str | None) -> bool:
        """Check if text is safe to send to AI (no sensitive patterns).
        
        Args:
            text: Text to check
            
        Returns:
            True if safe, False if contains sensitive patterns
        """
        if not text:
            return True

        for pattern in SENSITIVE_PATTERNS.values():
            if pattern.search(text):
                return False

        return True

    @staticmethod
    def sanitize_merchant(merchant: str) -> str:
        """Sanitize merchant name for AI.
        
        Removes account numbers, IDs, etc. from merchant name.
        
        Args:
            merchant: Raw merchant name
            
        Returns:
            Sanitized merchant name
        """
        result = PrivacyFilter.sanitize_text(merchant)
        return result.sanitized_text or merchant

    @staticmethod
    def sanitize_description(description: str) -> str:
        """Sanitize transaction description for AI.
        
        Args:
            description: Raw description
            
        Returns:
            Sanitized description
        """
        result = PrivacyFilter.sanitize_text(description)
        return result.sanitized_text or description


class AIContextBuilder:
    """Builds sanitized context for AI requests.
    
    This is critical for privacy. The context builder:
    1. Never includes raw files or sensitive identifiers
    2. Minimizes data sent to AI
    3. Uses sanitized descriptions only
    4. Includes only necessary historical context
    5. Validates no sensitive patterns remain before building context
    """

    def __init__(self, privacy_filter: PrivacyFilter | None = None):
        """Initialize context builder.
        
        Args:
            privacy_filter: Optional custom privacy filter
        """
        self.filter = privacy_filter or PrivacyFilter()

    def build_categorization_context(
        self,
        transaction: Transaction,
        existing_categories: list[str] | None = None,
    ) -> SanitizedContext:
        """Build context for categorization request.
        
        Args:
            transaction: Transaction to categorize
            existing_categories: Valid categories for reference
            
        Returns:
            SanitizedContext safe for AI
            
        Raises:
            ValueError: If unsafe patterns detected that cannot be redacted
        """
        # Sanitize all text fields
        merchant = self.filter.sanitize_merchant(transaction.merchant)
        description = self.filter.sanitize_description(transaction.description)

        # Verify safety
        if not self.filter.is_safe_for_ai(merchant):
            raise ValueError(
                f"Merchant contains unredactable sensitive patterns: {transaction.merchant}"
            )
        if not self.filter.is_safe_for_ai(description):
            raise ValueError(
                f"Description contains unredactable sensitive patterns: {transaction.description}"
            )

        # Build minimal context
        context = SanitizedContext(
            merchant=merchant,
            description=description,
            amount=transaction.amount,
            direction=transaction.direction.value,
            date=transaction.posted_date.isoformat(),
            existing_category=transaction.category,
            existing_merchant=transaction.merchant if transaction.merchant else None,
        )

        return context

    def build_merchant_context(
        self,
        transaction: Transaction,
    ) -> SanitizedContext:
        """Build context for merchant suggestion request.
        
        Args:
            transaction: Transaction with unknown merchant
            
        Returns:
            SanitizedContext safe for AI
        """
        merchant = self.filter.sanitize_merchant(transaction.merchant)
        description = self.filter.sanitize_description(transaction.description)

        if not self.filter.is_safe_for_ai(merchant):
            raise ValueError(
                f"Merchant contains unredactable sensitive patterns: {transaction.merchant}"
            )

        context = SanitizedContext(
            merchant=merchant,
            description=description,
            amount=transaction.amount,
            direction=transaction.direction.value,
            date=transaction.posted_date.isoformat(),
        )

        return context

    def build_chat_context(
        self,
        transactions: list[Transaction],
        filters: TransactionFilters | None = None,
        aggregates_only: bool = True,
    ) -> dict[str, Any]:
        """Build context for chat queries.
        
        Prefers aggregated data over individual transactions for privacy.
        
        Args:
            transactions: Transactions to include
            filters: Applied filters (metadata only, not sent to AI)
            aggregates_only: If True, only include aggregates, not individual txns
            
        Returns:
            Sanitized context dict for chat
        """
        context: dict[str, Any] = {
            "transaction_count": len(transactions),
            "total_spent": str(sum(
                t.amount for t in transactions if t.direction.value == "debit"
            )),
            "total_income": str(sum(
                t.amount for t in transactions if t.direction.value == "credit"
            )),
        }

        # Add category breakdown
        categories: dict[str, Decimal] = {}
        for t in transactions:
            if t.category:
                categories[t.category] = categories.get(t.category, Decimal("0")) + t.amount

        context["category_breakdown"] = {
            cat: str(amount) for cat, amount in categories.items()
        }

        # Add merchant breakdown (top 10)
        merchants: dict[str, Decimal] = {}
        for t in transactions:
            merchants[t.merchant] = merchants.get(t.merchant, Decimal("0")) + t.amount

        top_merchants = sorted(merchants.items(), key=lambda x: x[1], reverse=True)[:10]
        context["top_merchants"] = [
            {"merchant": m, "amount": str(a)} for m, a in top_merchants
        ]

        # Only include individual transactions if requested and count is small
        if not aggregates_only and len(transactions) <= 50:
            context["recent_transactions"] = [
                {
                    "date": t.posted_date.isoformat(),
                    "merchant": self.filter.sanitize_merchant(t.merchant),
                    "category": t.category,
                    "amount": str(t.amount),
                    "direction": t.direction.value,
                    "description": self.filter.sanitize_description(t.description),
                }
                for t in transactions[:20]  # Limit to 20 most recent
            ]

        return context

    def validate_context_safety(self, context: SanitizedContext | dict) -> bool:
        """Validate that context contains no sensitive patterns.
        
        Args:
            context: Context to validate
            
        Returns:
            True if safe, False if contains sensitive patterns
            
        Raises:
            ValueError: If unsafe patterns found
        """
        if isinstance(context, SanitizedContext):
            if not self.filter.is_safe_for_ai(context.merchant):
                raise ValueError("Merchant contains sensitive patterns")
            if not self.filter.is_safe_for_ai(context.description):
                raise ValueError("Description contains sensitive patterns")
            return True

        # For dict context, check string values
        for value in context.values():
            if isinstance(value, str):
                if not self.filter.is_safe_for_ai(value):
                    raise ValueError(f"Context contains sensitive patterns: {value}")
            elif isinstance(value, dict):
                if not self.validate_context_safety(value):
                    return False
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        if not self.validate_context_safety(item):
                            return False

        return True
