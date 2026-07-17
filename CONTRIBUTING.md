# Contributing

## Development setup

Use Python 3.11+ and install the development extra:

```powershell
python -m pip install -e ".[dev]"
python -m pytest
```

## Privacy rules

- Never persist raw CSV rows, raw descriptions, bank reference IDs, account numbers, UPI IDs, or tokens.
- Never add sensitive values to exceptions or logs. Use the import safe logger for import events.
- Add a regression test for every new sensitive-data pattern or persistence path.
- Do not commit `.env`, database files, archive files, virtual environments, or generated Python caches.

## Change quality

- Keep domain changes focused and type-compatible with Python 3.11.
- Add tests at the appropriate layer: unit, SQLite adapter, and end-to-end import integration where relevant.
- Run `python -m pytest` and `git diff --check` before opening a release change.
- Update `README.md`, `PRIVACY.md`, `SECURITY.md`, and `RELEASE_CHECKLIST.md` when behavior or operational assumptions change.
