"""Merchant Memory - Learning from user decisions and applying them to future transactions.

When a user confirms a merchant or category, Tally stores that decision.
Future transactions with similar merchant names automatically apply the
learned category and alias.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4

from backend.app.features.intelligence.models import MerchantMemory
from backend.app.features.transactions.models import Transaction


@dataclass(frozen=True)
class MerchantMemoryCandidate:
    """A candidate merchant for memory matching."""
    raw_merchant: str
    canonical: str
    category: str | None = None
    alias: str | None = None
    similarity_score: float = 0.0


class MerchantMemoryStore:
    """In-memory store of merchant memory decisions.
    
    In production, this would be backed by a repository that queries
    a database table.
    """

    def __init__(self):
        """Initialize memory store."""
        self.memories: dict[UUID, list[MerchantMemory]] = {}  # user_id -> memories

    def add_memory(
        self,
        user_id: UUID,
        merchant_raw: str,
        merchant_canonical: str,
        category: str | None = None,
        user_renamed_to: str | None = None,
    ) -> MerchantMemory:
        """Store a merchant decision.
        
        Args:
            user_id: User ID
            merchant_raw: Original merchant name from transaction
            merchant_canonical: Confirmed canonical merchant name
            category: Category assigned
            user_renamed_to: User's custom alias for merchant
            
        Returns:
            Stored MerchantMemory
        """
        memory = MerchantMemory(
            id=uuid4(),
            user_id=user_id,
            merchant_raw=merchant_raw.lower().strip(),
            merchant_canonical=merchant_canonical.lower().strip(),
            category=category,
            user_renamed_to=user_renamed_to,
            applied_count=1,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        if user_id not in self.memories:
            self.memories[user_id] = []

        self.memories[user_id].append(memory)
        return memory

    def find_memory(
        self,
        user_id: UUID,
        merchant: str,
    ) -> MerchantMemory | None:
        """Find merchant memory for exact match.
        
        Args:
            user_id: User ID
            merchant: Merchant name to lookup
            
        Returns:
            MerchantMemory if found, None otherwise
        """
        if user_id not in self.memories:
            return None

        merchant_lower = merchant.lower().strip()
        for memory in self.memories[user_id]:
            if memory.merchant_raw == merchant_lower:
                return memory

        return None

    def get_all_memories(self, user_id: UUID) -> list[MerchantMemory]:
        """Get all merchant memories for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            List of merchant memories
        """
        return self.memories.get(user_id, [])

    def increment_applied_count(self, memory_id: UUID, user_id: UUID) -> None:
        """Increment count of times memory was applied.
        
        Args:
            memory_id: Memory ID
            user_id: User ID
        """
        if user_id not in self.memories:
            return

        for memory in self.memories[user_id]:
            if memory.id == memory_id:
                # Create updated memory with incremented count
                updated = MerchantMemory(
                    id=memory.id,
                    user_id=memory.user_id,
                    merchant_raw=memory.merchant_raw,
                    merchant_canonical=memory.merchant_canonical,
                    category=memory.category,
                    user_renamed_to=memory.user_renamed_to,
                    applied_count=memory.applied_count + 1,
                    created_at=memory.created_at,
                    updated_at=datetime.now(UTC),
                )
                # Replace in list
                idx = self.memories[user_id].index(memory)
                self.memories[user_id][idx] = updated
                break


class MerchantMemoryEngine:
    """Engine for matching transactions against stored merchant memory."""

    def __init__(self, store: MerchantMemoryStore | None = None):
        """Initialize merchant memory engine.
        
        Args:
            store: Optional custom memory store
        """
        self.store = store or MerchantMemoryStore()

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two strings (simple Levenshtein).
        
        Args:
            text1: First string
            text2: Second string
            
        Returns:
            Similarity score 0.0 to 1.0
        """
        text1 = text1.lower().strip()
        text2 = text2.lower().strip()

        if text1 == text2:
            return 1.0

        # Simple substring matching
        if text1 in text2 or text2 in text1:
            return 0.8

        # Calculate basic Levenshtein distance
        if len(text1) == 0 or len(text2) == 0:
            return 0.0

        # Rough approximation
        common = sum(
            1 for c in text1 if c in text2
        ) / max(len(text1), len(text2))

        return common * 0.7  # Cap at 0.7 for partial matches

    def find_best_match(
        self,
        user_id: UUID,
        merchant: str,
        threshold: float = 0.7,
    ) -> MerchantMemoryCandidate | None:
        """Find best matching merchant memory.
        
        Args:
            user_id: User ID
            merchant: Merchant to find match for
            threshold: Minimum similarity (0.0 to 1.0)
            
        Returns:
            Best matching candidate or None
        """
        memories = self.store.get_all_memories(user_id)
        if not memories:
            return None

        best_match = None
        best_score = threshold

        for memory in memories:
            score = self._calculate_similarity(merchant, memory.merchant_raw)

            if score > best_score:
                best_score = score
                best_match = MerchantMemoryCandidate(
                    raw_merchant=merchant,
                    canonical=memory.merchant_canonical,
                    category=memory.category,
                    alias=memory.user_renamed_to,
                    similarity_score=score,
                )

        return best_match

    def find_exact_match(
        self,
        user_id: UUID,
        merchant: str,
    ) -> MerchantMemoryCandidate | None:
        """Find exact merchant memory match.
        
        Args:
            user_id: User ID
            merchant: Merchant to find
            
        Returns:
            Exact match candidate or None
        """
        memory = self.store.find_memory(user_id, merchant)
        if not memory:
            return None

        return MerchantMemoryCandidate(
            raw_merchant=merchant,
            canonical=memory.merchant_canonical,
            category=memory.category,
            alias=memory.user_renamed_to,
            similarity_score=1.0,
        )

    def apply_memory_to_transaction(
        self,
        transaction: Transaction,
        user_id: UUID,
        auto_apply_threshold: float = 0.95,
    ) -> tuple[Transaction, MerchantMemoryCandidate | None]:
        """Try to apply merchant memory to transaction.
        
        Args:
            transaction: Transaction to enhance
            user_id: User ID
            auto_apply_threshold: Minimum score to auto-apply (0.95 = very high confidence)
            
        Returns:
            Tuple of (possibly modified transaction, matching memory or None)
        """
        # First try exact match
        exact = self.find_exact_match(user_id, transaction.merchant)
        if exact:
            # Apply memory
            modified = Transaction.create(
                user_id=transaction.user_id,
                posted_date=transaction.posted_date,
                amount=transaction.amount,
                direction=transaction.direction,
                merchant=exact.canonical,
                description=transaction.description,
                category=exact.category or transaction.category,
                tags=transaction.tags,
                notes=transaction.notes,
                import_id=transaction.import_id,
                balance=transaction.balance,
                reference_number=transaction.reference_number,
            )
            return modified, exact

        # Try fuzzy match
        fuzzy = self.find_best_match(user_id, transaction.merchant, threshold=0.6)
        if fuzzy and fuzzy.similarity_score >= auto_apply_threshold:
            # High confidence - auto-apply
            modified = Transaction.create(
                user_id=transaction.user_id,
                posted_date=transaction.posted_date,
                amount=transaction.amount,
                direction=transaction.direction,
                merchant=fuzzy.canonical,
                description=transaction.description,
                category=fuzzy.category or transaction.category,
                tags=transaction.tags,
                notes=transaction.notes,
                import_id=transaction.import_id,
                balance=transaction.balance,
                reference_number=transaction.reference_number,
            )
            return modified, fuzzy

        # Return original transaction with potential match for user review
        return transaction, fuzzy if fuzzy else None

    def record_user_decision(
        self,
        user_id: UUID,
        merchant_raw: str,
        merchant_canonical: str,
        category: str | None = None,
        user_renamed_to: str | None = None,
    ) -> MerchantMemory:
        """Record user's decision about a merchant.
        
        Args:
            user_id: User ID
            merchant_raw: Raw merchant name from transaction
            merchant_canonical: Canonical name user confirmed
            category: Category user assigned
            user_renamed_to: User's custom alias
            
        Returns:
            Stored memory
        """
        return self.store.add_memory(
            user_id=user_id,
            merchant_raw=merchant_raw,
            merchant_canonical=merchant_canonical,
            category=category,
            user_renamed_to=user_renamed_to,
        )
