# Tally Finance Core

Tally is a privacy-first personal-finance domain library. It imports supported CSV bank statements, normalizes and deduplicates transactions, removes sensitive identifiers before persistence, and provides local analytics and privacy-filtered intelligence helpers.

## Release scope

This repository currently contains domain services and local SQLite/in-memory adapters. It does not expose a web server or mobile UI. API authentication, transport rate limiting, accessibility, and managed telemetry are therefore deployment concerns, not runnable features of this package.

## Quick start

Requires Python 3.11 or newer.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python -m pytest
```

To exercise the bounded import performance check:

```powershell
python -m pytest -m performance
```

## Privacy and security

- Source CSVs are staged in a controlled temporary directory and deleted after import; Archive Mode encrypts before retention.
- Descriptions and notes are redacted before persistence. Bank reference IDs are used only for deduplication and are never stored.
- Import logs redact sensitive fields and public import failures return only a stable error code.
- SQLite queries use bound parameters; the local adapter is appropriate for development and single-device use.

See [PRIVACY.md](PRIVACY.md), [SECURITY.md](SECURITY.md), and [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md) for operational requirements.

## Project layout

- `backend/app/features/imports`: statement import, validation, sanitization, and persistence.
- `backend/app/features/transactions`: local transaction and analytics services.
- `backend/app/features/intelligence`: privacy-filtered rules, confidence, and caching.
- `backend/tests`: unit, SQLite repository, integration, and performance checks.

## License

No license has been supplied for this repository. Confirm licensing before public distribution.
