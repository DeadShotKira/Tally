"""Logging utilities for the Intelligence Layer."""

import logging
from typing import Any
from uuid import UUID


logger = logging.getLogger(__name__)


def log_rule_match(rule_id: UUID, rule_name: str, transaction_id: UUID):
    """Log when a rule matches a transaction."""
    logger.info(
        "Rule matched",
        extra={
            "rule_id": str(rule_id),
            "rule_name": rule_name,
            "transaction_id": str(transaction_id),
            "event": "rule_match",
        },
    )


def log_ai_request(
    user_id: UUID,
    request_type: str,
    provider: str,
    model: str,
):
    """Log AI request (without sensitive data)."""
    logger.info(
        "AI request initiated",
        extra={
            "user_id": str(user_id),
            "request_type": request_type,
            "provider": provider,
            "model": model,
            "event": "ai_request",
        },
    )


def log_cache_hit(request_type: str, user_id: UUID):
    """Log cache hit."""
    logger.debug(
        "Cache hit",
        extra={
            "request_type": request_type,
            "user_id": str(user_id),
            "event": "cache_hit",
        },
    )


def log_merchant_memory_applied(
    merchant_raw: str,
    merchant_canonical: str,
    transaction_id: UUID,
):
    """Log a merchant-memory event without exposing merchant strings."""
    logger.debug(
        "Merchant memory applied",
        extra={
            "transaction_id": str(transaction_id),
            "event": "memory_applied",
        },
    )


def log_categorization(
    transaction_id: UUID,
    category: str | None,
    source: str,
    confidence: float,
):
    """Log transaction categorization."""
    logger.info(
        "Transaction categorized",
        extra={
            "transaction_id": str(transaction_id),
            "category": category,
            "source": source,
            "confidence": confidence,
            "event": "categorization",
        },
    )


def log_privacy_violation_prevented(
    violation_type: str,
    details: str,
):
    """Log when privacy violation is prevented."""
    logger.warning(
        "Privacy violation prevented",
        extra={
            "violation_type": violation_type,
            "event": "privacy_violation_prevented",
        },
    )
