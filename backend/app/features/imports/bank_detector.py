"""Bank format detection for CSV statement imports.

The detector scores each registered :class:`BankProfile` against the CSV
headers and text markers, returning the best match above a 0.70 confidence
threshold.  When no profile matches, a generic CSV fallback is attempted.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from io import StringIO

from .models import BankDetectionResult


@dataclass(frozen=True)
class BankProfile:
    code: str
    display_name: str
    required_headers: frozenset[str]
    optional_headers: frozenset[str] = frozenset()
    markers: frozenset[str] = frozenset()


class BankDetector:
    def __init__(self, profiles: tuple[BankProfile, ...] | None = None):
        self.profiles = profiles or DEFAULT_BANK_PROFILES

    def detect(self, csv_text: str) -> BankDetectionResult:
        headers = self._headers(csv_text)
        lowered_text = csv_text[:4096].lower()
        best: tuple[float, BankProfile, tuple[str, ...]] | None = None
        for profile in self.profiles:
            required_matches = profile.required_headers.intersection(headers)
            optional_matches = profile.optional_headers.intersection(headers)
            marker_matches = tuple(marker for marker in profile.markers if marker.lower() in lowered_text)
            if not profile.required_headers.issubset(headers):
                score = (len(required_matches) * 0.2) + (len(marker_matches) * 0.15)
            else:
                score = 0.75 + (len(optional_matches) * 0.05) + (len(marker_matches) * 0.05)
            reasons = tuple(sorted(required_matches | optional_matches)) + marker_matches
            if best is None or score > best[0]:
                best = (score, profile, reasons)

        if best and best[0] >= 0.70:
            score, profile, reasons = best
            return BankDetectionResult(profile.code, profile.display_name, min(score, 0.99), reasons)

        if self._looks_like_transaction_csv(headers):
            return BankDetectionResult("generic_csv", "Generic CSV", 0.50, ("generic transaction columns",), True)

        return BankDetectionResult("unknown", "Unknown Bank", 0.0, ("unsupported headers",), False)

    def _headers(self, csv_text: str) -> set[str]:
        sample = csv_text[:8192]
        try:
            dialect = csv.Sniffer().sniff(sample)
        except csv.Error:
            dialect = csv.excel
        reader = csv.reader(StringIO(csv_text), dialect)
        for row in reader:
            if row and any(cell.strip() for cell in row):
                return {self._normalize_header(cell) for cell in row}
        return set()

    @staticmethod
    def _normalize_header(value: str) -> str:
        return " ".join(value.strip().lower().replace("_", " ").split())

    @staticmethod
    def _looks_like_transaction_csv(headers: set[str]) -> bool:
        has_date = bool(headers.intersection({"date", "txn date", "transaction date", "value date"}))
        has_description = bool(headers.intersection({"description", "narration", "particulars", "details"}))
        has_amount = bool(headers.intersection({"amount", "debit", "credit", "withdrawal", "deposit"}))
        return has_date and has_description and has_amount


DEFAULT_BANK_PROFILES = (
    BankProfile(
        code="hdfc",
        display_name="HDFC Bank",
        required_headers=frozenset({"date", "narration"}),
        optional_headers=frozenset({"chq/ref no", "value date", "withdrawal amt", "deposit amt", "closing balance"}),
        markers=frozenset({"hdfc"}),
    ),
    BankProfile(
        code="icici",
        display_name="ICICI Bank",
        required_headers=frozenset({"transaction date", "transaction remarks"}),
        optional_headers=frozenset({"withdrawal amount", "deposit amount", "balance"}),
        markers=frozenset({"icici"}),
    ),
    BankProfile(
        code="sbi",
        display_name="State Bank of India",
        required_headers=frozenset({"txn date", "description"}),
        optional_headers=frozenset({"ref no./cheque no.", "debit", "credit", "balance"}),
        markers=frozenset({"state bank of india", "sbi"}),
    ),
    BankProfile(
        code="axis",
        display_name="Axis Bank",
        required_headers=frozenset({"tran date", "particulars"}),
        optional_headers=frozenset({"debit", "credit", "balance", "chq no"}),
        markers=frozenset({"axis bank"}),
    ),
)
