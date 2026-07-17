# Tally Blueprint

## Product Vision

Tally is a privacy-first personal finance application for people who want insight into their money without surrendering raw banking data. Users import statements, Tally extracts and normalizes transactions, deletes the original file by default, and then provides searchable history, analytics, budgeting foundations, merchant intelligence, and AI-assisted explanations.

The product philosophy is:

- Privacy before convenience.
- Local-first processing wherever practical.
- Store the minimum durable data needed for user value.
- Make sensitive-data handling explicit, observable, and configurable.
- Keep AI useful, constrained, and unable to see raw bank statements or banking identifiers.

### Goals

- Provide reliable transaction import from CSV first, then PDF.
- Normalize messy bank data into clean, searchable transaction records.
- Help users understand spending patterns, subscriptions, cash flow, and anomalies.
- Support offline access to previously synced transactions and settings.
- Allow optional cloud sync through Supabase without making cloud sync mandatory.
- Build a modular architecture that can support multiple banks, AI providers, and future platforms.

### Privacy-First Approach

Raw imported files are temporary by default. The import pipeline must parse, validate, normalize, sanitize, persist normalized transaction data, and then delete the source file. Sensitive identifiers such as account numbers, IFSC, UPI IDs, phone numbers, customer IDs, statement headers, and raw files must never be sent to AI services.

### Offline-First Approach

The mobile app should remain useful without a network connection. Authentication, cloud sync, and AI require connectivity, but viewing cached transactions, dashboard summaries, tags, settings, and import previews should work locally where feasible. Hive stores local read models and user preferences; Secure Storage stores secrets and tokens.

### AI Philosophy

AI is an assistant, not the source of truth. Deterministic rules, user preferences, and merchant memory take precedence over AI suggestions. AI receives only sanitized, minimal context and must produce explainable suggestions with confidence scores and fallback behavior.

## Scope

### Included Features

- Email/password authentication through Supabase Auth.
- CSV statement import.
- Local temporary file handling.
- Bank format detection.
- Transaction parsing, normalization, validation, and deduplication.
- Merchant resolution through aliases, rules, and optional AI assistance.
- Category assignment through rules, memory, and AI suggestions.
- Transaction timeline, search, filters, and detail views.
- Dashboard analytics for spend, income, categories, merchants, and trends.
- AI chat over sanitized transaction summaries.
- Privacy modes: Maximum Privacy Mode, Cloud Sync Mode, Archive Mode.
- Settings for privacy, sync, export, theme, and account.

### Excluded Features

- Direct bank account linking.
- Payment initiation.
- Investment trading.
- Tax filing.
- Credit scoring.
- Shared family accounts in initial release.
- Real-time bank synchronization.
- AI access to raw files or sensitive banking identifiers.

### Future Roadmap

- PDF statement import with secure extraction.
- Multi-bank parser library.
- Budgets and savings goals.
- Recurring transaction and subscription detection.
- Family/shared spaces with explicit consent.
- Export to CSV/XLSX.
- Provider-agnostic AI routing.
- On-device ML for merchant cleanup and categorization.
- Web dashboard.

## Target Users

- Students: need simple spending awareness, category summaries, and low-friction imports.
- Professionals: need recurring expense detection, cash-flow visibility, and privacy.
- Families: need household expense views and future shared budgets.
- Freelancers: need income/expense separation, client/vendor tracking, and exportable records.

## Core Modules

### Authentication

Responsible for signup, login, logout, password reset, session refresh, secure token storage, and account deletion. Authentication uses Supabase Auth and FastAPI verifies JWTs for backend access.

### Statement Import

Responsible for selecting files, copying them into temporary app-controlled storage, detecting bank format, parsing rows, producing previews, handling errors, and deleting original files after successful import according to privacy mode.

### Transaction Engine

Responsible for normalized transaction records, duplicate detection, search indexing, tags, categories, rule application, balance handling, and local/cloud synchronization.

### Merchant Intelligence

Responsible for canonical merchants, aliases, merchant memory, user corrections, confidence scoring, and unknown merchant review flows.

### Analytics

Responsible for aggregations, time-series summaries, category trends, merchant spend, income/expense summaries, anomaly candidates, and dashboard read models.

### Dashboard

Responsible for presenting the user’s financial snapshot: current month spend, income, category breakdown, notable merchants, recent transactions, and alerts.

### AI Layer

Responsible for privacy-filtered prompt construction, sanitized context generation, provider abstraction, confidence scoring, AI chat, merchant suggestions, category suggestions, and fallback when AI is disabled or unavailable.

### Privacy Engine

Responsible for sensitive-field detection, redaction, mode behavior, file deletion, archive encryption, AI guardrails, sync eligibility, and audit events.

### Settings

Responsible for user preferences, privacy mode, theme, sync settings, import behavior, notification preferences, AI opt-in, and account controls.

## Non-Functional Requirements

- Performance: import 10,000 CSV rows on a mid-range device without UI lockup; dashboard summaries should load from local cache in under 500 ms.
- Scalability: backend data model supports millions of transactions across users with per-user isolation and indexed queries.
- Offline support: cached transaction history and analytics remain readable offline; writes queue locally when supported.
- Security: JWT verification, Supabase RLS, encrypted token storage, least-privilege service keys, input validation, and secure file handling.
- Maintainability: feature-based folders, clean boundaries, repository pattern, typed contracts, migrations, and architecture decision records.
- Testability: parser fixtures, unit tests, repository tests, API contract tests, widget tests, integration tests, and privacy regression tests.
- Accessibility: Material 3 semantics, text scaling, screen-reader labels, contrast compliance, keyboard-friendly flows where applicable.

## Folder Structure

```text
Tally/
  docs/
    BLUEPRINT.md
    PRODUCT.md
    SYSTEM_ARCHITECTURE.md
    DATABASE.md
    API.md
    AUTHENTICATION.md
    IMPORT_PIPELINE.md
    AI_PIPELINE.md
    PRIVACY.md
    UI_DESIGN.md
    USER_FLOWS.md
    SECURITY.md
    DEVELOPMENT_PLAN.md
  mobile/
    lib/
      app/
      core/
      features/
        auth/
        import/
        transactions/
        merchants/
        analytics/
        dashboard/
        ai_chat/
        settings/
        privacy/
      shared/
    assets/
    test/
    integration_test/
  backend/
    app/
      api/
      core/
      domain/
      services/
      repositories/
      schemas/
      workers/
    migrations/
    tests/
  shared/
    contracts/
    schemas/
  scripts/
  config/
```

Documentation may live at the root during Phase 0. Once implementation begins, the `docs/` directory becomes the canonical location.

## Coding Standards

- Naming: `snake_case` for Python, SQL, and API fields; `lowerCamelCase` for Dart variables; `UpperCamelCase` for Dart classes and Python domain classes.
- Formatting: use `dart format`, Python formatter/linter, SQL migration formatter, and consistent Markdown headings.
- Architecture: Clean Architecture with feature modules, dependency inversion, repository interfaces, and explicit DTO/domain boundaries.
- Dependency injection: Riverpod providers on mobile; FastAPI dependency providers on backend.
- Error handling: typed domain failures mapped to user-safe messages and API error codes.
- Logging: structured logs without sensitive values; never log raw file contents, tokens, account numbers, UPI IDs, or prompts containing sensitive data.
- Comments: explain non-obvious business rules, parser assumptions, and privacy constraints.
- Testing: all privacy filters, parsers, duplicate detection, API contracts, and AI prompt builders require regression tests.

## Database Standards

- Table names use plural `snake_case`.
- Primary keys use UUIDs.
- Foreign keys are explicit and indexed.
- Tables include `created_at` and `updated_at`.
- User-owned tables include `user_id`.
- Soft deletes use nullable `deleted_at` where recovery or audit matters.
- Use partial unique indexes for active records where soft deletes exist.
- Migrations are forward-only, reviewed, and include rollback notes.
- Supabase RLS must prevent cross-user reads and writes.

## API Standards

- REST under `/api/v1`.
- JSON request and response bodies.
- Success envelope: `{ "data": ..., "meta": ... }`.
- Error envelope: `{ "error": { "code": "...", "message": "...", "details": ... } }`.
- Authenticated endpoints require `Authorization: Bearer <jwt>`.
- Pagination uses `limit`, `cursor`, and `next_cursor`.
- Filtering uses explicit query parameters.
- API contracts are versioned; breaking changes require a new version.

## UI Principles

- Use Flutter Material 3.
- Mobile-first layouts with responsive adaptations for tablets.
- Consistent spacing scale: 4, 8, 12, 16, 24, 32.
- Typography follows Material 3 roles.
- Color communicates category, status, and risk without relying solely on hue.
- Dark mode is first-class.
- Every interactive element has accessible labels and sufficient tap targets.
- Empty, loading, and error states are designed for every screen.

## Privacy Rules

### Maximum Privacy Mode

- Default mode.
- Raw statement files are deleted after successful import.
- No cloud transaction sync unless explicitly enabled.
- AI is disabled by default or receives only manually approved sanitized summaries.
- Local cache may exist, protected by device security and app controls.
- Import logs contain counts and parser diagnostics only.

### Cloud Sync Mode

- Normalized transaction data syncs to Supabase.
- Raw files are still deleted after import.
- AI remains privacy-filtered and never receives sensitive identifiers.
- RLS and backend authorization enforce user isolation.
- Local cache mirrors synced data for offline reading.

### Archive Mode

- User explicitly chooses to retain original statements.
- Files are encrypted before storage.
- Archive keys are stored in Secure Storage or platform keychain.
- Archived files are never sent to AI.
- User can delete archives independently of normalized transactions.

## AI Rules

AI must never receive:

- Account numbers.
- IFSC codes.
- UPI IDs.
- Phone numbers.
- Customer IDs.
- Statement headers.
- Raw files.
- Full unfiltered transaction descriptions if they contain sensitive identifiers.

AI may receive:

- Sanitized merchant names.
- Amounts, dates, transaction direction, category, and tags.
- Aggregated summaries.
- User-authored questions after privacy filtering.
- Redacted transaction context with stable synthetic identifiers.

## Definition of Done

A feature is complete when:

- Requirements and privacy behavior are documented.
- Domain, API, UI, and data contracts are aligned.
- Sensitive-data paths are reviewed.
- Unit, integration, and privacy tests pass.
- Offline behavior is defined and tested where applicable.
- Loading, empty, error, and accessibility states are handled.
- Logs and analytics contain no sensitive data.
- Documentation is updated.
