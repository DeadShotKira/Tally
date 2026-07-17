from __future__ import annotations

import csv
from abc import ABC, abstractmethod
from io import StringIO

from .errors import ParserError
from .models import ParsedStatement, ParsedTransactionRow


class StatementParser(ABC):
    source_type = "csv"

    @abstractmethod
    def parse(self, text: str) -> ParsedStatement:
        raise NotImplementedError


class GenericCsvParser(StatementParser):
    FIELD_ALIASES = {
        "date": ("date", "txn date", "transaction date", "tran date", "value date"),
        "description": ("description", "narration", "particulars", "details", "transaction remarks"),
        "debit": ("debit", "withdrawal", "withdrawal amt", "withdrawal amount"),
        "credit": ("credit", "deposit", "deposit amt", "deposit amount"),
        "amount": ("amount", "transaction amount"),
        "direction": ("type", "dr/cr", "debit/credit"),
        "balance": ("balance", "closing balance", "available balance"),
        "reference": ("reference", "ref no", "ref no./cheque no.", "chq/ref no", "chq no"),
        "notes": ("notes", "remarks"),
    }

    def parse(self, text: str) -> ParsedStatement:
        try:
            sample = text[:8192]
            dialect = csv.Sniffer().sniff(sample)
        except csv.Error:
            dialect = csv.excel

        try:
            reader = csv.DictReader(StringIO(text), dialect=dialect)
            if reader.fieldnames is None:
                raise ParserError(technical_detail="CSV has no header row")
            normalized_headers = {self._normalize_header(header): header for header in reader.fieldnames}
            rows: list[ParsedTransactionRow] = []
            warnings: list[str] = []
            for index, raw in enumerate(reader, start=2):
                if not raw or not any((value or "").strip() for value in raw.values()):
                    continue
                row = {self._normalize_header(key): (value or "").strip() for key, value in raw.items() if key is not None}
                parsed = ParsedTransactionRow(
                    row_number=index,
                    raw_date=self._get(row, "date"),
                    raw_description=self._get(row, "description"),
                    raw_debit=self._get(row, "debit"),
                    raw_credit=self._get(row, "credit"),
                    raw_amount=self._get(row, "amount"),
                    raw_direction=self._get(row, "direction"),
                    raw_balance=self._get(row, "balance"),
                    raw_reference=self._get(row, "reference"),
                    raw_notes=self._get(row, "notes"),
                    raw_data={key: row.get(key, "") for key in normalized_headers},
                )
                rows.append(parsed)
            if not rows:
                warnings.append("CSV did not contain transaction rows.")
            return ParsedStatement(rows=tuple(rows), warnings=tuple(warnings))
        except ParserError:
            raise
        except csv.Error as exc:
            raise ParserError(technical_detail=str(exc)) from exc

    def _get(self, row: dict[str, str], canonical: str) -> str | None:
        for alias in self.FIELD_ALIASES[canonical]:
            value = row.get(alias)
            if value:
                return value
        return None

    @staticmethod
    def _normalize_header(value: str) -> str:
        return " ".join(value.strip().lower().replace("_", " ").split())


class HDFCParser(GenericCsvParser):
    pass


class ICICIParser(GenericCsvParser):
    pass


class SBIParser(GenericCsvParser):
    pass


class AxisParser(GenericCsvParser):
    pass


class StatementParserFactory:
    def __init__(self):
        self._parsers: dict[str, StatementParser] = {
            "hdfc": HDFCParser(),
            "icici": ICICIParser(),
            "sbi": SBIParser(),
            "axis": AxisParser(),
            "generic_csv": GenericCsvParser(),
        }

    def for_bank(self, bank_code: str) -> StatementParser:
        return self._parsers.get(bank_code, self._parsers["generic_csv"])
