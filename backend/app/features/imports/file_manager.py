from __future__ import annotations

import hashlib
import os
import shutil
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from uuid import uuid4

from cryptography.fernet import Fernet

from .errors import FileTooLargeError, TemporaryFileError, UnsupportedFileError
from .models import PrivacyAction, TemporaryStatement


class TemporaryStatementFileManager:
    def __init__(
        self,
        *,
        temp_root: Path | None = None,
        archive_root: Path | None = None,
        max_size_bytes: int = 20 * 1024 * 1024,
        archive_key: bytes | None = None,
    ):
        self.temp_root = temp_root or Path(tempfile.gettempdir()) / "tally-imports"
        self.archive_root = archive_root or Path(tempfile.gettempdir()) / "tally-archives"
        self.max_size_bytes = max_size_bytes
        self.archive_key = archive_key or Fernet.generate_key()

    def prepare_csv(self, source_path: Path, original_filename: str | None = None) -> TemporaryStatement:
        path = Path(source_path)
        if path.suffix.lower() != ".csv":
            raise UnsupportedFileError(technical_detail=f"Unsupported extension: {path.suffix}")
        if not path.exists() or not path.is_file():
            raise UnsupportedFileError(technical_detail="Source path does not exist or is not a file")
        size = path.stat().st_size
        if size <= 0:
            raise UnsupportedFileError(technical_detail="CSV file is empty")
        if size > self.max_size_bytes:
            raise FileTooLargeError(technical_detail=f"CSV size {size} exceeds {self.max_size_bytes}")

        self.temp_root.mkdir(parents=True, exist_ok=True)
        temp_path = self.temp_root / f"{uuid4()}.csv"
        try:
            shutil.copyfile(path, temp_path)
        except OSError as exc:
            raise TemporaryFileError(technical_detail=str(exc)) from exc

        return TemporaryStatement(
            path=temp_path,
            original_filename=original_filename or path.name,
            size_bytes=size,
            sha256=self.sha256(temp_path),
        )

    def read_text(self, statement: TemporaryStatement) -> str:
        try:
            return statement.path.read_text(encoding="utf-8-sig")
        except UnicodeDecodeError:
            return statement.path.read_text(encoding="latin-1")
        except OSError as exc:
            raise TemporaryFileError(technical_detail=str(exc)) from exc

    def delete(self, path: Path) -> PrivacyAction:
        try:
            if path.exists():
                path.unlink()
            return PrivacyAction(action="deleted_temporary_statement", details="Original temporary statement deleted.")
        except OSError as exc:
            raise TemporaryFileError(technical_detail=str(exc)) from exc

    def archive_encrypted(self, statement: TemporaryStatement) -> tuple[Path, PrivacyAction]:
        self.archive_root.mkdir(parents=True, exist_ok=True)
        archive_path = self.archive_root / f"{statement.sha256[:16]}-{uuid4()}.csv.fernet"
        encrypted = Fernet(self.archive_key).encrypt(statement.path.read_bytes())
        archive_path.write_bytes(encrypted)
        return archive_path, PrivacyAction(
            action="encrypted_archive_created",
            details="Original statement encrypted and stored in archive mode.",
        )

    def cleanup_old_temp_files(self, *, older_than: timedelta = timedelta(hours=24)) -> int:
        if not self.temp_root.exists():
            return 0
        cutoff = datetime.now().timestamp() - older_than.total_seconds()
        deleted = 0
        for candidate in self.temp_root.glob("*"):
            if candidate.is_file() and candidate.stat().st_mtime < cutoff:
                candidate.unlink(missing_ok=True)
                deleted += 1
        return deleted

    @staticmethod
    def sha256(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()
