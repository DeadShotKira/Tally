"""Repository interfaces for Intelligence Layer persistence.

These interfaces define how Intelligence Layer entities persist to the database.
In production, these would be implemented using Supabase or similar.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any
from uuid import UUID

from backend.app.features.intelligence.models import (
    Insight,
    MerchantMemory,
    RecurringTransaction,
    Rule,
)


class MerchantMemoryRepository(ABC):
    """Repository for merchant memory persistence."""

    @abstractmethod
    async def save(self, memory: MerchantMemory) -> MerchantMemory:
        """Save merchant memory."""
        pass

    @abstractmethod
    async def find_by_id(self, memory_id: UUID, user_id: UUID) -> MerchantMemory | None:
        """Find memory by ID."""
        pass

    @abstractmethod
    async def find_by_merchant(
        self,
        user_id: UUID,
        merchant_raw: str,
    ) -> MerchantMemory | None:
        """Find memory by raw merchant name."""
        pass

    @abstractmethod
    async def find_all_by_user(self, user_id: UUID) -> list[MerchantMemory]:
        """Find all memories for a user."""
        pass

    @abstractmethod
    async def update(self, memory: MerchantMemory) -> MerchantMemory:
        """Update merchant memory."""
        pass

    @abstractmethod
    async def delete(self, memory_id: UUID, user_id: UUID) -> None:
        """Delete merchant memory."""
        pass


class RuleRepository(ABC):
    """Repository for rule persistence."""

    @abstractmethod
    async def save(self, rule: Rule) -> Rule:
        """Save rule."""
        pass

    @abstractmethod
    async def find_by_id(self, rule_id: UUID, user_id: UUID) -> Rule | None:
        """Find rule by ID."""
        pass

    @abstractmethod
    async def find_all_by_user(self, user_id: UUID) -> list[Rule]:
        """Find all enabled rules for a user."""
        pass

    @abstractmethod
    async def find_by_priority(self, user_id: UUID) -> list[Rule]:
        """Find all rules sorted by priority."""
        pass

    @abstractmethod
    async def update(self, rule: Rule) -> Rule:
        """Update rule."""
        pass

    @abstractmethod
    async def delete(self, rule_id: UUID, user_id: UUID) -> None:
        """Delete rule."""
        pass

    @abstractmethod
    async def set_enabled(self, rule_id: UUID, user_id: UUID, enabled: bool) -> None:
        """Enable or disable rule."""
        pass


class RecurringTransactionRepository(ABC):
    """Repository for recurring transaction persistence."""

    @abstractmethod
    async def save(self, recurring: RecurringTransaction) -> RecurringTransaction:
        """Save recurring transaction."""
        pass

    @abstractmethod
    async def find_by_id(
        self,
        recurring_id: UUID,
        user_id: UUID,
    ) -> RecurringTransaction | None:
        """Find recurring transaction by ID."""
        pass

    @abstractmethod
    async def find_all_by_user(self, user_id: UUID) -> list[RecurringTransaction]:
        """Find all recurring transactions for user."""
        pass

    @abstractmethod
    async def find_by_merchant(
        self,
        user_id: UUID,
        merchant: str,
    ) -> list[RecurringTransaction]:
        """Find recurring transactions for merchant."""
        pass

    @abstractmethod
    async def update(self, recurring: RecurringTransaction) -> RecurringTransaction:
        """Update recurring transaction."""
        pass

    @abstractmethod
    async def delete(self, recurring_id: UUID, user_id: UUID) -> None:
        """Delete recurring transaction."""
        pass


class InsightRepository(ABC):
    """Repository for insight persistence."""

    @abstractmethod
    async def save(self, insight: Insight) -> Insight:
        """Save insight."""
        pass

    @abstractmethod
    async def find_by_id(self, insight_id: UUID, user_id: UUID) -> Insight | None:
        """Find insight by ID."""
        pass

    @abstractmethod
    async def find_recent_by_user(
        self,
        user_id: UUID,
        limit: int = 20,
    ) -> list[Insight]:
        """Find recent insights for user."""
        pass

    @abstractmethod
    async def find_by_type(
        self,
        user_id: UUID,
        insight_type: str,
    ) -> list[Insight]:
        """Find insights of specific type."""
        pass

    @abstractmethod
    async def delete(self, insight_id: UUID, user_id: UUID) -> None:
        """Delete insight."""
        pass

    @abstractmethod
    async def delete_old_insights(self, days: int = 30) -> int:
        """Delete insights older than N days. Returns count deleted."""
        pass


class InMemoryMerchantMemoryRepository(MerchantMemoryRepository):
    """In-memory implementation for testing."""

    def __init__(self):
        """Initialize in-memory repository."""
        self.storage: dict[UUID, MerchantMemory] = {}

    async def save(self, memory: MerchantMemory) -> MerchantMemory:
        """Save merchant memory."""
        self.storage[memory.id] = memory
        return memory

    async def find_by_id(self, memory_id: UUID, user_id: UUID) -> MerchantMemory | None:
        """Find memory by ID."""
        memory = self.storage.get(memory_id)
        if memory and memory.user_id == user_id:
            return memory
        return None

    async def find_by_merchant(
        self,
        user_id: UUID,
        merchant_raw: str,
    ) -> MerchantMemory | None:
        """Find memory by raw merchant name."""
        merchant_lower = merchant_raw.lower().strip()
        for memory in self.storage.values():
            if (
                memory.user_id == user_id
                and memory.merchant_raw == merchant_lower
            ):
                return memory
        return None

    async def find_all_by_user(self, user_id: UUID) -> list[MerchantMemory]:
        """Find all memories for a user."""
        return [m for m in self.storage.values() if m.user_id == user_id]

    async def update(self, memory: MerchantMemory) -> MerchantMemory:
        """Update merchant memory."""
        self.storage[memory.id] = memory
        return memory

    async def delete(self, memory_id: UUID, user_id: UUID) -> None:
        """Delete merchant memory."""
        if memory_id in self.storage:
            del self.storage[memory_id]


class InMemoryRuleRepository(RuleRepository):
    """In-memory implementation for testing."""

    def __init__(self):
        """Initialize in-memory repository."""
        self.storage: dict[UUID, Rule] = {}

    async def save(self, rule: Rule) -> Rule:
        """Save rule."""
        self.storage[rule.id] = rule
        return rule

    async def find_by_id(self, rule_id: UUID, user_id: UUID) -> Rule | None:
        """Find rule by ID."""
        rule = self.storage.get(rule_id)
        if rule and rule.user_id == user_id:
            return rule
        return None

    async def find_all_by_user(self, user_id: UUID) -> list[Rule]:
        """Find all enabled rules for a user."""
        return [r for r in self.storage.values() if r.user_id == user_id and r.enabled]

    async def find_by_priority(self, user_id: UUID) -> list[Rule]:
        """Find all rules sorted by priority."""
        rules = [r for r in self.storage.values() if r.user_id == user_id and r.enabled]
        return sorted(rules, key=lambda r: r.priority)

    async def update(self, rule: Rule) -> Rule:
        """Update rule."""
        self.storage[rule.id] = rule
        return rule

    async def delete(self, rule_id: UUID, user_id: UUID) -> None:
        """Delete rule."""
        if rule_id in self.storage:
            del self.storage[rule_id]

    async def set_enabled(self, rule_id: UUID, user_id: UUID, enabled: bool) -> None:
        """Enable or disable rule."""
        rule = self.storage.get(rule_id)
        if rule and rule.user_id == user_id:
            updated = Rule(
                id=rule.id,
                user_id=rule.user_id,
                name=rule.name,
                description=rule.description,
                rule_type=rule.rule_type,
                priority=rule.priority,
                conditions=rule.conditions,
                action=rule.action,
                enabled=enabled,
                created_at=rule.created_at,
                updated_at=rule.updated_at,
            )
            self.storage[rule_id] = updated
