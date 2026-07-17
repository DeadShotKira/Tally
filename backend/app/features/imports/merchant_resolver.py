"""Heuristic merchant name resolver for the imports pipeline.

Strips payment-mode noise words (UPI, NEFT, IMPS, …) and numeric tokens
from a sanitized transaction description, then title-cases the first four
remaining tokens to produce a human-readable merchant name.

This is a fast, deterministic fallback.  The Intelligence Layer's
:class:`MerchantMemoryEngine` and AI providers improve on this later.
"""

from __future__ import annotations

import re


class MerchantResolver:
    UNKNOWN_MERCHANT = "Unknown Merchant"
    NOISE_WORDS = {
        "upi",
        "neft",
        "imps",
        "rtgs",
        "pos",
        "atm",
        "debit",
        "credit",
        "payment",
        "transfer",
        "to",
        "from",
        "ref",
    }

    def resolve(self, sanitized_description: str) -> str:
        cleaned = re.sub(r"\[[A-Z_]+_REDACTED\]", " ", sanitized_description)
        cleaned = re.sub(r"[^A-Za-z0-9 &.\-]", " ", cleaned)
        tokens = [token for token in cleaned.split() if token.lower() not in self.NOISE_WORDS and not token.isdigit()]
        if not tokens:
            return self.UNKNOWN_MERCHANT
        merchant = " ".join(tokens[:4]).strip(" .-")
        return merchant.title() if len(merchant) >= 2 else self.UNKNOWN_MERCHANT
