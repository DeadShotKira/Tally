"""AI Response Cache - Caches AI suggestions to minimize repeated requests.

Cache keys are based on sanitized inputs only - never include sensitive
banking information in cache keys.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any
from uuid import UUID

from backend.app.features.intelligence.models import (
    AICategory,
    AIMerchant,
    ConfidenceLevel,
    SanitizedContext,
)


@dataclass
class CacheEntry:
    """A cached AI response."""
    key: str
    response_type: str  # "category", "merchant", "chat"
    data: dict[str, Any]
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    expires_at: datetime = field(default_factory=lambda: datetime.now(UTC) + timedelta(days=30))
    hit_count: int = 0

    def is_expired(self) -> bool:
        """Check if cache entry has expired."""
        return datetime.now(UTC) > self.expires_at


class AICache:
    """In-memory cache for AI responses.
    
    In production, this would be backed by Redis or similar.
    """

    def __init__(self, max_entries: int = 10000, ttl_days: int = 30):
        """Initialize cache.
        
        Args:
            max_entries: Maximum number of entries
            ttl_days: Time-to-live for entries in days
        """
        self.cache: dict[str, CacheEntry] = {}
        self.max_entries = max_entries
        self.ttl_days = ttl_days

    def _generate_key(
        self,
        request_type: str,
        user_id: UUID,
        data_hash: str,
    ) -> str:
        """Generate cache key.
        
        Args:
            request_type: Type of request ("category", "merchant", "chat")
            user_id: User ID
            data_hash: Hash of sanitized input
            
        Returns:
            Cache key
        """
        return f"{request_type}:{user_id}:{data_hash}"

    def _hash_sanitized_context(self, context: SanitizedContext) -> str:
        """Hash sanitized context for cache key.
        
        Args:
            context: Sanitized context
            
        Returns:
            SHA256 hash of context
        """
        # Create canonical representation
        data = {
            "merchant": context.merchant.lower().strip(),
            "description": context.description.lower().strip(),
            "amount_rounded": str(round(context.amount, -1)),  # Round to nearest 10
            "direction": context.direction,
        }

        # Hash it
        json_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(json_str.encode()).hexdigest()[:16]

    def get_category(
        self,
        user_id: UUID,
        context: SanitizedContext,
    ) -> AICategory | None:
        """Get cached category suggestion.
        
        Args:
            user_id: User ID
            context: Sanitized context
            
        Returns:
            Cached AICategory or None if not found
        """
        data_hash = self._hash_sanitized_context(context)
        key = self._generate_key("category", user_id, data_hash)

        if key not in self.cache:
            return None

        entry = self.cache[key]
        if entry.is_expired():
            del self.cache[key]
            return None

        # Record hit
        entry.hit_count += 1

        data = entry.data
        return AICategory(
            category=data["category"],
            confidence=float(data["confidence"]),
            confidence_level=ConfidenceLevel(data["confidence_level"]),
            reasoning=data.get("reasoning"),
        )

    def set_category(
        self,
        user_id: UUID,
        context: SanitizedContext,
        suggestion: AICategory,
    ) -> None:
        """Cache a category suggestion.
        
        Args:
            user_id: User ID
            context: Sanitized context
            suggestion: AI suggestion to cache
        """
        # Check cache size
        if len(self.cache) >= self.max_entries:
            self._evict_oldest()

        data_hash = self._hash_sanitized_context(context)
        key = self._generate_key("category", user_id, data_hash)

        entry = CacheEntry(
            key=key,
            response_type="category",
            data={
                "category": suggestion.category,
                "confidence": suggestion.confidence,
                "confidence_level": suggestion.confidence_level.value,
                "reasoning": suggestion.reasoning,
            },
            expires_at=datetime.now(UTC) + timedelta(days=self.ttl_days),
        )

        self.cache[key] = entry

    def get_merchant(
        self,
        user_id: UUID,
        context: SanitizedContext,
    ) -> AIMerchant | None:
        """Get cached merchant suggestion.
        
        Args:
            user_id: User ID
            context: Sanitized context
            
        Returns:
            Cached AIMerchant or None if not found
        """
        data_hash = self._hash_sanitized_context(context)
        key = self._generate_key("merchant", user_id, data_hash)

        if key not in self.cache:
            return None

        entry = self.cache[key]
        if entry.is_expired():
            del self.cache[key]
            return None

        entry.hit_count += 1

        data = entry.data
        return AIMerchant(
            merchant=data["merchant"],
            confidence=float(data["confidence"]),
            confidence_level=ConfidenceLevel(data["confidence_level"]),
            reasoning=data.get("reasoning"),
        )

    def set_merchant(
        self,
        user_id: UUID,
        context: SanitizedContext,
        suggestion: AIMerchant,
    ) -> None:
        """Cache a merchant suggestion.
        
        Args:
            user_id: User ID
            context: Sanitized context
            suggestion: AI suggestion to cache
        """
        if len(self.cache) >= self.max_entries:
            self._evict_oldest()

        data_hash = self._hash_sanitized_context(context)
        key = self._generate_key("merchant", user_id, data_hash)

        entry = CacheEntry(
            key=key,
            response_type="merchant",
            data={
                "merchant": suggestion.merchant,
                "confidence": suggestion.confidence,
                "confidence_level": suggestion.confidence_level.value,
                "reasoning": suggestion.reasoning,
            },
            expires_at=datetime.now(UTC) + timedelta(days=self.ttl_days),
        )

        self.cache[key] = entry

    def clear_user_cache(self, user_id: UUID) -> int:
        """Clear all cache entries for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            Number of entries cleared
        """
        user_prefix = f":{user_id}:"
        keys_to_delete = [k for k in self.cache if user_prefix in k]

        for key in keys_to_delete:
            del self.cache[key]

        return len(keys_to_delete)

    def clear_all(self) -> int:
        """Clear entire cache.
        
        Returns:
            Number of entries cleared
        """
        count = len(self.cache)
        self.cache.clear()
        return count

    def cleanup_expired(self) -> int:
        """Remove expired entries.
        
        Returns:
            Number of entries removed
        """
        expired_keys = [
            k for k, v in self.cache.items() if v.is_expired()
        ]

        for key in expired_keys:
            del self.cache[key]

        return len(expired_keys)

    def _evict_oldest(self) -> None:
        """Evict oldest entry when cache is full."""
        if not self.cache:
            return

        oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k].created_at)
        del self.cache[oldest_key]

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics.
        
        Returns:
            Dictionary with cache stats
        """
        total_hits = sum(e.hit_count for e in self.cache.values())
        return {
            "total_entries": len(self.cache),
            "max_entries": self.max_entries,
            "total_hits": total_hits,
            "average_hits_per_entry": (
                total_hits / len(self.cache) if self.cache else 0
            ),
            "expired_entries": sum(1 for e in self.cache.values() if e.is_expired()),
        }
