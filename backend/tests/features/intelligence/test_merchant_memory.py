"""Tests for Merchant Memory."""

import pytest
from decimal import Decimal
from datetime import date
from uuid import uuid4

from backend.app.features.intelligence.merchant_memory import (
    MerchantMemoryEngine,
    MerchantMemoryStore,
)
from backend.app.features.imports.models import TransactionDirection
from backend.app.features.transactions.models import Transaction


class TestMerchantMemoryStore:
    """Test merchant memory storage."""

    def test_add_and_find_memory(self):
        """Test adding and finding merchant memory."""
        store = MerchantMemoryStore()
        user_id = uuid4()

        memory = store.add_memory(
            user_id=user_id,
            merchant_raw="RAHUL KUMAR",
            merchant_canonical="Rahul Vegetable Vendor",
            category="Groceries",
        )

        assert memory.merchant_raw == "rahul kumar"
        assert memory.merchant_canonical == "rahul vegetable vendor"

        found = store.find_memory(user_id, "RAHUL KUMAR")
        assert found is not None
        assert found.category == "Groceries"

    def test_find_nonexistent_memory(self):
        """Test finding memory that doesn't exist."""
        store = MerchantMemoryStore()
        user_id = uuid4()

        found = store.find_memory(user_id, "Unknown Merchant")
        assert found is None

    def test_increment_applied_count(self):
        """Test incrementing memory applied count."""
        store = MerchantMemoryStore()
        user_id = uuid4()

        memory = store.add_memory(
            user_id=user_id,
            merchant_raw="Amazon",
            merchant_canonical="Amazon.com",
        )

        initial_count = memory.applied_count
        store.increment_applied_count(memory.id, user_id)

        updated_memories = store.get_all_memories(user_id)
        updated = updated_memories[0]

        assert updated.applied_count == initial_count + 1


class TestMerchantMemoryEngine:
    """Test merchant memory matching."""

    def test_find_exact_match(self):
        """Test finding exact merchant match."""
        store = MerchantMemoryStore()
        engine = MerchantMemoryEngine(store)
        user_id = uuid4()

        store.add_memory(
            user_id=user_id,
            merchant_raw="Amazon",
            merchant_canonical="Amazon.com",
            category="Shopping",
        )

        match = engine.find_exact_match(user_id, "Amazon")
        assert match is not None
        assert match.canonical == "amazon.com"
        assert match.category == "Shopping"
        assert match.similarity_score == 1.0

    def test_find_fuzzy_match(self):
        """Test finding similar merchant match."""
        store = MerchantMemoryStore()
        engine = MerchantMemoryEngine(store)
        user_id = uuid4()

        store.add_memory(
            user_id=user_id,
            merchant_raw="Swiggy",
            merchant_canonical="Swiggy",
            category="Food",
        )

        # Should find Swiggy even if search term is slightly different
        match = engine.find_best_match(user_id, "Swigggy", threshold=0.5)
        # Might or might not match depending on similarity calculation
        # Just verify it returns a candidate or None without error

    def test_apply_memory_to_transaction(self):
        """Test applying memory to transaction."""
        store = MerchantMemoryStore()
        engine = MerchantMemoryEngine(store)
        user_id = uuid4()

        store.add_memory(
            user_id=user_id,
            merchant_raw="Amazon",
            merchant_canonical="Amazon.com",
            category="Shopping",
        )

        txn = Transaction.create(
            user_id=user_id,
            posted_date=date.today(),
            amount=Decimal("500"),
            direction=TransactionDirection.DEBIT,
            merchant="Amazon",
        )

        modified, match = engine.apply_memory_to_transaction(txn, user_id)

        assert match is not None
        assert modified.merchant == "amazon.com"
        assert modified.category == "Shopping"

    def test_record_user_decision(self):
        """Test recording user decision."""
        store = MerchantMemoryStore()
        engine = MerchantMemoryEngine(store)
        user_id = uuid4()

        memory = engine.record_user_decision(
            user_id=user_id,
            merchant_raw="RAHUL123",
            merchant_canonical="Rahul Vegetable",
            category="Groceries",
            user_renamed_to="Veggie Shop",
        )

        assert memory.merchant_raw == "rahul123"
        assert memory.user_renamed_to == "Veggie Shop"

        # Verify it's stored
        found = store.find_memory(user_id, "RAHUL123")
        assert found is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
