# Phase 5 Release Checklist

## Verified in this repository

- [x] CSV imports have a 20 MB size limit, temporary-file cleanup, SHA-256 deduplication, and bounded streaming file hashing.
- [x] SQLite persistence uses parameterized values and a per-user unique dedupe index.
- [x] Sensitive identifiers are redacted before descriptions or notes are persisted; reference IDs are not retained.
- [x] Import and intelligence logging avoids raw descriptions, merchants, file hashes, and failure details.
- [x] Privacy, SQLite, integration, and bounded 10,000-row import tests are present.
- [x] Package metadata, environment template, contributor guidance, and release documentation are present.

## Deployment gates (must be completed by the host application)

- [ ] Verify JWT signature, issuer, audience, expiry, and authenticated user-to-record mapping.
- [ ] Enforce database RLS and use a managed database backup/restore schedule; validate a restore before launch.
- [ ] Apply per-user and per-IP limits at the API gateway, with stricter quotas for AI and import endpoints.
- [ ] Configure privacy-safe error telemetry with retention, access controls, and alerting.
- [ ] Complete the mobile/web accessibility audit (keyboard/screen-reader flow, contrast, text scaling, and error announcements).
- [ ] Store archive keys in platform secure storage or managed secrets; rotate and test recovery procedures.
- [ ] Run the full test suite in the release CI environment using the supported Python version.

## Backup and export plan

The current SQLite adapter is a local development/single-device store and does not implement backup/export. A production host must provide authenticated export of sanitized normalized transactions only (CSV/JSON), encrypted backups, a documented retention period, and a restore drill. Raw statement files and archive encryption keys must never be included in ordinary exports.
