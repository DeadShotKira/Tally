# Development Plan

## Phase 1: Foundations

Objectives: set up Flutter, FastAPI, Supabase schema, auth, project structure, CI, and documentation placement.

Tasks: create repos/folders, configure formatting/linting, implement auth skeleton, create migrations, define shared contracts, add test harnesses.

Dependencies: Phase 0 documents.

Acceptance criteria: app launches, backend health endpoint works, auth bootstrap works, migrations apply, CI runs.

Estimated effort: 1-2 weeks.

Constraints: no import or AI behavior until privacy foundations exist.

## Phase 2: CSV Import and Transactions

Objectives: import CSV statements into normalized transactions.

Tasks: file picker, temporary storage, parser adapters, normalization, sanitization, dedupe, import preview, transaction list/detail.

Dependencies: auth, schema, local storage.

Acceptance criteria: supported CSV imports successfully, raw temp files deleted by default, duplicate detection works, tests cover sensitive redaction.

Estimated effort: 2-4 weeks.

Constraints: no raw file upload to backend.

## Phase 3: Analytics and Merchant Intelligence

Objectives: turn transaction history into useful summaries.

Tasks: merchant aliases, category rules, dashboard summaries, filters/search, tags, analytics endpoints, local read models.

Dependencies: transaction engine.

Acceptance criteria: dashboard loads from cache, analytics match transaction data, merchant corrections affect future imports.

Estimated effort: 2-3 weeks.

Constraints: analytics must not depend on AI.

## Phase 4: AI Layer

Objectives: add privacy-preserving AI suggestions and chat.

Tasks: context builder, sensitive-pattern rejection, AI adapter, merchant/category suggestions, chat UI, confidence scoring, caching.

Dependencies: privacy engine, analytics, transaction data.

Acceptance criteria: automated tests prove forbidden fields are not sent to AI; AI can be disabled; low-confidence results require confirmation.

Estimated effort: 2-3 weeks.

Constraints: AI receives sanitized context only.

## Phase 5: Hardening and Release

Objectives: prepare production-grade release.

Tasks: accessibility audit, performance profiling, security review, rate limiting, error telemetry, backup/export planning, documentation updates.

Dependencies: complete feature set.

Acceptance criteria: release checklist passes, privacy tests pass, import performance target met, security findings resolved or accepted.

Estimated effort: 2 weeks.

Constraints: no release if privacy guarantees are unverified.
