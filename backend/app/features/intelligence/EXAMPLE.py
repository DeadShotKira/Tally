"""Integration example showing complete Intelligence Layer workflow.

This demonstrates how all components work together to categorize a transaction
while maintaining privacy and ensuring user control.
"""

from __future__ import annotations

import asyncio
from datetime import date
from decimal import Decimal
from uuid import uuid4

# Import all Intelligence Layer components
from backend.app.features.intelligence.cache import AICache
from backend.app.features.intelligence.categorization_service import (
    CategorizationService,
)
from backend.app.features.intelligence.confidence_engine import ConfidenceEngine
from backend.app.features.intelligence.context_builder import AIContextBuilder
from backend.app.features.intelligence.merchant_memory import MerchantMemoryEngine
from backend.app.features.intelligence.models import (
    AICategory,
    ConfidenceLevel,
    Rule,
)
from backend.app.features.intelligence.providers import MockAIProvider
from backend.app.features.intelligence.rule_engine import RuleEngine
from backend.app.features.imports.models import TransactionDirection
from backend.app.features.transactions.models import Transaction


async def example_workflow():
    """Demonstrate complete Intelligence Layer workflow."""

    print("=" * 70)
    print("PHASE 4: INTELLIGENCE LAYER - INTEGRATION EXAMPLE")
    print("=" * 70)

    # Setup
    user_id = uuid4()
    print(f"\n📝 User ID: {user_id}\n")

    # Create sample transaction
    transaction = Transaction.create(
        user_id=user_id,
        posted_date=date.today(),
        amount=Decimal("450.50"),
        direction=TransactionDirection.DEBIT,
        merchant="RAHUL KUMAR VEG VENDOR",
        description="Weekly grocery shopping at market",
    )

    print(f"Transaction Details:")
    print(f"  Merchant: {transaction.merchant}")
    print(f"  Amount: ₹{transaction.amount}")
    print(f"  Description: {transaction.description}")
    print()

    # Step 1: Create components
    print("🔧 Initializing Intelligence Layer components...")
    rule_engine = RuleEngine()
    merchant_memory_engine = MerchantMemoryEngine()
    ai_provider = MockAIProvider()
    context_builder = AIContextBuilder()
    confidence_engine = ConfidenceEngine()
    ai_cache = AICache()
    print("   ✅ All components initialized\n")

    # Step 2: Setup rules (deterministic layer)
    print("📋 Setting up deterministic rules...")
    grocery_rule = Rule.build_exact_match_rule(
        user_id=user_id,
        merchant="AMAZON",
        category="Shopping",
    )
    rules = [grocery_rule]
    print(f"   ✅ {len(rules)} rule(s) loaded\n")

    # Step 3: Setup merchant memory
    print("🧠 Teaching merchant memory...")
    # Record a previous decision
    memory = merchant_memory_engine.record_user_decision(
        user_id=user_id,
        merchant_raw="RAHUL KUMAR",
        merchant_canonical="Rahul Vegetable Vendor",
        category="Groceries",
        user_renamed_to="Veggie Shop",
    )
    print(f"   ✅ Learned: {memory.merchant_raw} → {memory.merchant_canonical}")
    print(f"      Category: {memory.category}\n")

    # Step 4: Build categorization service
    print("🤖 Creating categorization service...")
    categorization_service = CategorizationService(
        rule_engine=rule_engine,
        merchant_memory_engine=merchant_memory_engine,
        ai_provider=ai_provider,
        context_builder=context_builder,
        confidence_engine=confidence_engine,
    )
    print("   ✅ Service ready\n")

    # Step 5: Categorize transaction
    print("⚙️  Running categorization workflow...")
    print("   Step 1: Checking rules...")

    result = await categorization_service.categorize(
        transaction=transaction,
        user_id=user_id,
        rules=rules,
        existing_categories=["Groceries", "Food", "Shopping", "Other"],
        allow_ai=True,
    )

    print(f"   ✅ Result: {result.category}")
    print(f"      Source: {result.source}")
    print(f"      Confidence: {result.confidence:.2f} ({result.confidence_level.value})")
    print(f"      Auto-applied: {result.auto_applied}")
    print(f"      Reasoning: {result.reasoning}\n")

    # Step 6: Show privacy filtering
    print("🔒 Privacy Filtering Demonstration:")
    from backend.app.features.intelligence.context_builder import PrivacyFilter

    test_texts = [
        "Account 123456789012",
        "UPI: user@bank.com",
        "Call 9876543210",
        "Safe merchant name",
    ]

    for text in test_texts:
        sanitized = PrivacyFilter.sanitize_text(text)
        safety = PrivacyFilter.is_safe_for_ai(text)
        print(f"   Input: {text}")
        print(f"   Safe: {safety}")
        if sanitized.has_unsafe_patterns:
            print(f"   Sanitized: {sanitized.sanitized_text}")
        print()

    # Step 7: Show caching
    print("💾 Cache Demonstration:")
    stats = ai_cache.get_stats()
    print(f"   Cache entries: {stats['total_entries']}")
    print(f"   Cache capacity: {stats['max_entries']}")
    print(f"   Total hits: {stats['total_hits']}\n")

    # Step 8: Show confidence levels
    print("📊 Confidence Levels:")
    for score in [0.95, 0.75, 0.50]:
        level = confidence_engine.calculate_confidence_level(score)
        breakdown = confidence_engine.evaluate_confidence_breakdown(score)
        print(f"   Score {score:.2f}: {level.value} level")
        print(f"      Auto-apply: {breakdown['auto_apply']}")
        print(f"      Requires confirmation: {breakdown['requires_confirmation']}")
        print()

    # Step 9: Summary
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"""
✅ Privacy-First Approach:
   • AI received only sanitized context
   • No account numbers, UPI IDs, or sensitive data transmitted
   • All patterns validated before sending to AI provider

✅ Confidence Scoring:
   • Suggestions include confidence levels (HIGH/MEDIUM/LOW)
   • Low-confidence results require user confirmation
   • Users maintain full control over categorization

✅ Deterministic Rules:
   • Rules executed before AI
   • Provides explainable, reproducible results
   • No AI dependency for common patterns

✅ Merchant Memory:
   • Previous decisions learned and reused
   • Similarity matching for fuzzy lookups
   • Confidence-based auto-application

✅ Performance:
   • Responses cached to minimize API calls
   • Rules evaluated in priority order
   • Efficient in-memory storage

✅ User Control:
   • Users can create custom rules
   • Users approve/reject suggestions
   • Feedback improves future suggestions
""")
    print("=" * 70)


if __name__ == "__main__":
    # Run async example
    asyncio.run(example_workflow())
