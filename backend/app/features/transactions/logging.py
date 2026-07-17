from __future__ import annotations

from backend.app.features.imports.logging import SafeImportLogger


class SafeFinanceLogger(SafeImportLogger):
    """Structured logger for finance modules that inherits sensitive-field redaction."""
