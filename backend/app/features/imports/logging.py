from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Any

SENSITIVE_KEYS = {
    "description",
    "sanitized_description",
    "raw_data",
    "account_number",
    "upi_id",
    "phone",
    "customer_id",
    "token",
}


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
