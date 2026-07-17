# System Architecture

## Overview

Tally uses a Flutter mobile client, FastAPI backend, Supabase PostgreSQL, SQLAlchemy, Riverpod, Hive, Secure Storage, and an AI service behind a provider abstraction. The system is modular, privacy-first, and offline-capable where practical.

```mermaid
flowchart LR
  User[User] --> Mobile[Flutter Mobile App]
  Mobile --> Hive[Hive Local Cache]
  Mobile --> Secure[Secure Storage]
  Mobile --> API[FastAPI API]
  API --> DB[(Supabase PostgreSQL)]
  API --> Auth[Supabase Auth / JWT Verification]
  API --> AIProxy[AI Service Adapter]
  AIProxy --> Provider[AI Provider]
  Mobile --> Importer[Local Import Pipeline]
  Importer --> Sanitizer[Privacy Engine]
  Sanitizer --> Hive
  Sanitizer --> API
```

## Flutter

Flutter owns the user experience, local import preparation, offline read models, secure token storage, and privacy mode controls. Riverpod provides dependency injection and state management. Hive stores cached transactions, dashboard summaries, import drafts, and non-secret preferences. Secure Storage stores tokens and encryption keys.

## FastAPI

FastAPI owns authenticated API contracts, transaction persistence, server-side validation, analytics queries, AI request mediation, and sync coordination. It must never accept raw statement uploads in the initial CSV workflow unless a future explicitly documented upload feature is approved.

## Supabase

Supabase provides PostgreSQL, authentication, and RLS. Database access is isolated per user. Application migrations define schema changes. Backend service credentials are never shipped to the mobile app.

## AI Service

The AI service is accessed through an adapter that accepts only sanitized context. Provider-specific clients are hidden behind an interface so future providers can be swapped without changing product behavior.

## Authentication

```mermaid
sequenceDiagram
  participant App as Flutter App
  participant Supa as Supabase Auth
  participant API as FastAPI
  participant DB as PostgreSQL
  App->>Supa: Login credentials
  Supa-->>App: Access JWT + refresh token
  App->>API: Bearer access JWT
  API->>Supa: Verify JWT claims/JWKS
  API->>DB: Query rows scoped by user_id
  DB-->>API: User-owned data
  API-->>App: Response envelope
```

## Import Pipeline

CSV files are processed locally first. The app copies a selected file into temporary storage, detects bank format, parses rows, normalizes transactions, sanitizes descriptions, checks duplicates, stores normalized records, and deletes the temporary source file by default.

## Analytics Pipeline

```mermaid
flowchart TD
  Tx[Transactions] --> LocalAgg[Local Aggregates]
  Tx --> ServerAgg[Server Aggregates]
  LocalAgg --> Dashboard[Dashboard View Models]
  ServerAgg --> Dashboard
  Dashboard --> User[User]
```

Analytics must be reproducible from transactions. Cached summaries are read models, not authoritative records.

## Privacy Pipeline

```mermaid
flowchart TD
  Raw[Raw Statement File] --> Temp[Temporary Storage]
  Temp --> Parse[Parser]
  Parse --> Normalize[Normalization]
  Normalize --> Detect[Sensitive Field Detection]
  Detect --> Redact[Redaction/Sanitization]
  Redact --> Store[Store Normalized Data]
  Store --> Delete[Delete Raw File]
  Redact --> AIContext[AI-Safe Context]
```

## Module Interaction

```mermaid
flowchart LR
  Auth --> Transactions
  Import --> Privacy
  Privacy --> Transactions
  Transactions --> Merchants
  Merchants --> Analytics
  Transactions --> Analytics
  Analytics --> Dashboard
  Transactions --> AI
  Merchants --> AI
  Privacy --> AI
  Settings --> Privacy
  Settings --> AI
```

## Component Responsibilities

- Mobile presentation: screens, navigation, local state, accessibility.
- Mobile domain layer: use cases and domain entities.
- Mobile data layer: repositories, API clients, Hive stores, secure storage.
- Backend API layer: routing, authentication, validation, response shaping.
- Backend service layer: business workflows and policy enforcement.
- Backend repository layer: SQLAlchemy persistence.
- Database: durable normalized data with RLS.
- AI adapter: sanitized context only, provider abstraction, retries, confidence parsing.
