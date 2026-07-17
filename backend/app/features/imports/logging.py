"""Privacy-aware structured logger for the imports pipeline.

All log fields are passed through ``_redact`` before emission so that
sensitive identifiers listed in :data:`SENSITIVE_KEYS` never appear in
log output, regardless of the caller.
"""

from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Any

SENSITIVE_KEYS: frozenset[str] = frozenset({
    "description",
    "sanitized_description",
    "raw_data",
    "account_number",
    "upi_id",
    "phone",
    "customer_id",
    "token",
    # Identifiers that, while not raw PII, could be used to re-identify users
    # or map logs back to specific file uploads.
    "filename",
    "file_hash",
    "technical_detail",
    "technical_details",
})


class SafeImportLogger:
    def __init__(self, logger: logging.Logger | None = None):
        self._logger = logger or logging.getLogger("tally.imports")
        if not self._logger.handlers:
            self._logger.addHandler(logging.NullHandler())

    def info(self, event: str, **fields: Any) -> None:
        self._logger.info(event, extra={"tally": self._redact(fields)})

    def warning(self, event: str, **fields: Any) -> None:
        self._logger.warning(event, extra={"tally": self._redact(fields)})

    def error(self, event: str, **fields: Any) -> None:
        self._logger.error(event, extra={"tally": self._redact(fields)})

    def _redact(self, fields: Mapping[str, Any]) -> dict[str, Any]:
        safe: dict[str, Any] = {}
        for key, value in fields.items():
            safe[key] = "[REDACTED]" if key in SENSITIVE_KEYS else value
        return safe
