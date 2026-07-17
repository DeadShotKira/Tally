"""Domain models for the Intelligence Layer."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal
from enum import Enum
from uuid import UUID, uuid4


class ConfidenceLevel(str, Enum):
    """Confidence level for AI suggestions."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class AIProviderType(str, Enum):
    """Supported AI providers."""
    OPENAI = "openai"
    GEMINI = "gemini"
    OLLAMA = "ollama"


@dataclass(frozen=True)
class AICategory:
    """Suggested category from AI with confidence."""
    category: str
    confidence: float  # 0.0 to 1.0
    confidence_level: ConfidenceLevel
    reasoning: str | None = None


@dataclass(frozen=True)
class AIMerchant:
    """Suggested merchant from AI with confidence."""
    merchant: str
    confidence: float  # 0.0 to 1.0
    confidence_level: ConfidenceLevel
    reasoning: str | None = None


@dataclass(frozen=True)
class RecurringTransaction:
    """A detected recurring transaction or subscription."""
    id: UUID
    user_id: UUID
    merchant: str
    category: str | None
    amount: Decimal
    average_days_between: int
    last_occurrence_date: str  # ISO format date
    transaction_count: int
    confidence: float  # 0.0 to 1.0
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass(frozen=True)
class Insight:
    """A proactive financial insight."""
    id: UUID
    user_id: UUID
    insight_type: str  # e.g., "spending_increase", "subscription_detected", "anomaly"
    title: str
    description: str
    severity: str  # info, warning, alert
    related_metric: str | None = None
    metadata: dict[str, str] = field(default_factory=dict)
    generated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass(frozen=True)
class MerchantMemory:
    """Stored user decision about a merchant."""
    id: UUID
    user_id: UUID
    merchant_raw: str  # Original merchant name from transaction
    merchant_canonical: str  # User-confirmed canonical name
    category: str | None = None  # Suggested or user-assigned category
    user_renamed_to: str | None = None  # User's custom alias
    applied_count: int = 0  # How many times this memory has been applied
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass(frozen=True)
class Rule:
    """A deterministic categorization or merchant rule."""
    id: UUID
    user_id: UUID
    name: str
    description: str | None
    rule_type: str  # "merchant_match", "merchant_pattern", "amount_threshold", etc.
    priority: int  # Lower = higher priority
    conditions: dict  # Pattern matching or threshold conditions
    action: dict  # What to do when rule matches (category, merchant, tags)
    enabled: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @staticmethod
    def build_exact_match_rule(
        user_id: UUID,
        merchant: str,
        category: str,
        priority: int = 10,
    ) -> Rule:
        """Create an exact merchant match rule."""
        return Rule(
            id=uuid4(),
            user_id=user_id,
            name=f"Exact match: {merchant} → {category}",
            description=f"Exact merchant match for '{merchant}'",
            rule_type="merchant_exact",
            priority=priority,
            conditions={"merchant": merchant, "match_type": "exact"},
            action={"category": category},
            enabled=True,
        )

    @staticmethod
    def build_pattern_rule(
        user_id: UUID,
        pattern: str,
        category: str,
        pattern_type: str = "merchant_contains",
        priority: int = 20,
    ) -> Rule:
        """Create a pattern-based rule (contains, prefix, suffix)."""
        return Rule(
            id=uuid4(),
            user_id=user_id,
            name=f"Pattern match: {pattern} → {category}",
            description=f"Pattern match ({pattern_type}) for '{pattern}'",
            rule_type=pattern_type,
            priority=priority,
            conditions={"pattern": pattern, "pattern_type": pattern_type},
            action={"category": category},
            enabled=True,
        )

    @staticmethod
    def build_amount_threshold_rule(
        user_id: UUID,
        amount_threshold: Decimal,
        operator: str,
        flag_for_review: bool = True,
        priority: int = 30,
    ) -> Rule:
        """Create an amount threshold rule."""
        return Rule(
            id=uuid4(),
            user_id=user_id,
            name=f"Amount threshold: {operator} {amount_threshold}",
            description=f"Flag transactions where amount {operator} {amount_threshold}",
            rule_type="amount_threshold",
            priority=priority,
            conditions={"threshold": str(amount_threshold), "operator": operator},
            action={"flag_for_review": flag_for_review},
            enabled=True,
        )


@dataclass(frozen=True)
class SanitizedContext:
    """Sanitized context for AI processing."""
    merchant: str
    description: str
    amount: Decimal
    direction: str  # "debit" or "credit"
    date: str  # ISO format date
    existing_category: str | None = None
    existing_merchant: str | None = None
    historical_context: str | None = None


@dataclass(frozen=True)
class AIRequest:
    """A request to the AI provider."""
    user_id: UUID
    request_type: str  # "categorize", "merchant", "chat", "insight"
    context: SanitizedContext | dict  # Depends on request_type
    model: str | None = None
    temperature: float | None = None
    max_tokens: int | None = None


@dataclass(frozen=True)
class AIResponse:
    """Response from AI provider."""
    request_id: UUID
    provider: str
    model: str
    result: dict  # Provider-specific result
    usage_tokens: int | None = None
    latency_ms: int | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass(frozen=True)
class ChatMessage:
    """A message in AI chat conversation."""
    id: UUID
    user_id: UUID
    conversation_id: UUID
    role: str  # "user", "assistant", "system"
    content: str
    context_used: dict | None = None  # Sanitized data sent to AI
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass(frozen=True)
class ChatConversation:
    """A chat conversation with AI."""
    id: UUID
    user_id: UUID
    title: str | None = None
    messages: tuple[ChatMessage, ...] = ()
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
