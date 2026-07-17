"""Bounded performance regression coverage for the local CSV import flow."""

from __future__ import annotations

import tempfile
import time
from pathlib import Path
from uuid import uuid4

import pytest
from cryptography.fernet import Fernet

from backend.app.features.imports.file_manager import TemporaryStatementFileManager
from backend.app.features.imports.models import ImportRequest, ImportStatus
from backend.app.features.imports.repository import InMemoryImportRepository
from backend.app.features.imports.service import build_default_import_service


@pytest.mark.performance
def test_imports_ten_thousand_rows_within_release_budget() -> None:
    """Guard against accidental quadratic work in the standard import path."""
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        source = root / "statement.csv"
        rows = ["Date,Description,Amount,Type,Reference"]
        rows.extend(
            f"2026-06-{(index % 28) + 1:02d},Merchant {index},-{index + 1}.00,debit,REF-{index}"
            for index in range(10_000)
        )
        source.write_text("\n".join(rows), encoding="utf-8")
        file_manager = TemporaryStatementFileManager(
            temp_root=root / "temp", archive_root=root / "archive", archive_key=Fernet.generate_key()
        )
        service = build_default_import_service(InMemoryImportRepository(), file_manager)

        started = time.perf_counter()
        result = service.import_csv(ImportRequest(user_id=uuid4(), source_path=source))
        elapsed = time.perf_counter() - started

        assert result.status is ImportStatus.COMPLETED
        assert result.imported_transactions == 10_000
        assert elapsed < 10.0
