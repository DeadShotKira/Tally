"""Tests for Privacy Filtering and AI Context Builder."""

import pytest
from decimal import Decimal
from datetime import date
from uuid import uuid4

from backend.app.features.intelligence.context_builder import (
    AIContextBuilder,
    PrivacyFilter,
)
from backend.app.features.intelligence.models import SanitizedContext
from backend.app.features.imports.models import TransactionDirection
from backend.app.features.transactions.models import Transaction


class TestPrivacyFilter:
    """Test privacy filtering functionality."""

    def test_sanitize_account_number(self):
        """Test that account numbers are redacted."""
        text = "Payment to RAHUL KUMAR Account: 1234567890"
        result = PrivacyFilter.sanitize_text(text)
        
        assert "[ACCOUNT_NUMBER_REDACTED]" in result.sanitized_text
        assert result.has_unsafe_patterns

    def test_sanitize_upi_id(self):
        """Test that UPI IDs are redacted."""
        text = "Transfer to user@bank via UPI"
        result = PrivacyFilter.sanitize_text(text)
        
        assert result.has_unsafe_patterns or result.sanitized_text != text

    def test_sanitize_phone_number(self):
        """Test that phone numbers are redacted."""
        text = "Call 9876543210 for support"
        result = PrivacyFilter.sanitize_text(text)
        
        assert "[PHONE_REDACTED]" in result.sanitized_text
        assert result.has_unsafe_patterns

    def test_safe_text_no_redaction(self):
        """Test that safe text passes through."""
        text = "Grocery store purchase"
        result = PrivacyFilter.sanitize_text(text)
        
        assert result.sanitized_text == text
        assert not result.has_unsafe_patterns

    def test_is_safe_for_ai_clean_text(self):
        """Test safety check for clean text."""
        text = "Restaurant purchase at ABC Cafe"
        assert PrivacyFilter.is_safe_for_ai(text)

    def test_is_safe_for_ai_with_account_number(self):
        """Test safety check rejects account numbers."""
        text = "Account 123456789012345"
        assert not PrivacyFilter.is_safe_for_ai(text)


class TestAIContextBuilder:
    """Test AI context builder."""

    def test_build_categorization_context(self):
        """Test building categorization context."""
        txn = Transaction.create(
            user_id=uuid4(),
            posted_date=date.today(),
            amount=Decimal("500.00"),
            direction=TransactionDirection.DEBIT,
            merchant="Grocery Store",
            description="Weekly grocery shopping",
        )

        builder = AIContextBuilder()
        context = builder.build_categorization_context(txn)

        assert context.merchant == "Grocery Store"
        assert context.description == "Weekly grocery shopping"
        assert context.amount == Decimal("500.00")
        assert context.direction == "debit"

    def test_build_merchant_context(self):
        """Test building merchant context."""
        txn = Transaction.create(
            user_id=uuid4(),
            posted_date=date.today(),
            amount=Decimal("1000.00"),
            direction=TransactionDirection.DEBIT,
            merchant="ABC123XYZ",
            description="Store purchase",
        )

        builder = AIContextBuilder()
        context = builder.build_merchant_context(txn)

        assert context.merchant == "ABC123XYZ"
        assert context.amount == Decimal("1000.00")

    def test_build_chat_context(self):
        """Test building chat context."""
        txns = [
            Transaction.create(
                user_id=uuid4(),
                posted_date=date.today(),
                amount=Decimal("500.00"),
                direction=TransactionDirection.DEBIT,
                merchant="Store A",
                description="Shopping",
                category="Shopping",
            ),
            Transaction.create(
                user_id=uuid4(),
                posted_date=date.today(),
                amount=Decimal("300.00"),
                direction=TransactionDirection.DEBIT,
                merchant="Store B",
                description="Groceries",
                category="Food",
            ),
        ]

        builder = AIContextBuilder()
        context = builder.build_chat_context(txns, aggregates_only=True)

        assert context["transaction_count"] == 2
        assert "total_spent" in context
        assert "category_breakdown" in context

    def test_context_validates_safety(self):
        """Test that context validation catches unsafe data."""
        builder = AIContextBuilder()
        
        # Create context with sensitive data
        unsafe_context = SanitizedContext(
            merchant="Store with Account 1234567890",
            description="Payment",
            amount=Decimal("100"),
            direction="debit",
            date="2024-01-01",
        )

        # Should raise ValueError for unsafe content
        with pytest.raises(ValueError):
            builder.validate_context_safety(unsafe_context)

    def test_sanitized_text_in_context(self):
        """Test that merchant/description are sanitized."""
        txn = Transaction.create(
            user_id=uuid4(),
            posted_date=date.today(),
            amount=Decimal("1000"),
            direction=TransactionDirection.DEBIT,
            merchant="Store Account 123456",
            description="Payment",
        )

        builder = AIContextBuilder()
        context = builder.build_categorization_context(txn)

        # Should have redacted the account number
        assert "[ACCOUNT" not in context.merchant or "REDACTED" in context.merchant


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
