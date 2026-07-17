from __future__ import annotations

import re

from .models import PrivacyResult


class PrivacyEngine:
    PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
        ("IFSC", re.compile(r"\b[A-Z]{4}0[A-Z0-9]{6}\b", re.IGNORECASE)),
        ("UPI", re.compile(r"\b[\w.\-]{2,}@[a-z][a-z0-9.\-]{2,}\b", re.IGNORECASE)),
        ("PHONE", re.compile(r"(?<!\d)(?:\+91[-\s]?)?[6-9]\d{9}(?!\d)")),
        ("ACCOUNT", re.compile(r"\b(?:a/c|acct|account|acc(?:ount)? no\.?)\s*[:\-]?\s*\d{6,18}\b", re.IGNORECASE)),
        ("CUSTOMER_ID", re.compile(r"\b(?:customer|cust)\s*(?:id|no)\s*[:\-]?\s*[A-Z0-9]{4,20}\b", re.IGNORECASE)),
        ("LONG_NUMBER", re.compile(r"\b\d{12,18}\b")),
        ("BRANCH", re.compile(r"\bbranch\s*[:\-]?\s*[A-Z0-9 .,\-]{3,40}", re.IGNORECASE)),
        ("STATEMENT_HEADER", re.compile(r"\b(statement\s+(?:summary|period)|opening\s+balance|closing\s+balance)\b", re.IGNORECASE)),
    )

    def sanitize_description(self, description: str) -> PrivacyResult:
        sanitized = description
        redactions: list[str] = []
        for label, pattern in self.PATTERNS:
            if pattern.search(sanitized):
                sanitized = pattern.sub(f"[{label}_REDACTED]", sanitized)
                redactions.append(label)
        sanitized = " ".join(sanitized.split())
        return PrivacyResult(sanitized_description=sanitized[:240], redactions=tuple(dict.fromkeys(redactions)))

    def assert_safe_for_storage(self, value: str) -> None:
        result = self.sanitize_description(value)
        if result.redactions:
            raise ValueError("Sensitive data remains after sanitization.")
