# REST API Contracts

## Standards

- Base path: `/api/v1`.
- Authentication: `Authorization: Bearer <access_jwt>` unless noted.
- Success: `{ "data": ..., "meta": {} }`.
- Error: `{ "error": { "code": "...", "message": "...", "details": {} } }`.
- Pagination: `limit`, `cursor`, `next_cursor`.
- Timestamps: ISO 8601 UTC.

Common errors: `401 unauthorized`, `403 forbidden`, `404 not_found`, `409 conflict`, `422 validation_error`, `429 rate_limited`, `500 internal_error`.

## Auth

### POST /auth/session

Purpose: exchange/validate Supabase session for app profile bootstrap.

Authentication: Bearer JWT.

Request: `{ "device_id": "string" }`

Response: `{ "data": { "user": { "id": "uuid", "email": "string" }, "settings": {} } }`

Validation: valid JWT, known or creatable user profile.

### POST /auth/logout

Purpose: invalidate app-side device session metadata.

Authentication: required.

Request: `{ "device_id": "string" }`

Response: `{ "data": { "logged_out": true } }`

## Transactions

### GET /transactions

Purpose: list transactions.

Authentication: required.

Query: `limit`, `cursor`, `from_date`, `to_date`, `category_id`, `merchant_id`, `direction`, `tag_id`, `search`.

Response: `{ "data": [{ "id": "uuid", "posted_date": "date", "description": "string", "amount": 123.45, "direction": "debit" }], "meta": { "next_cursor": "string" } }`

Validation: date range valid; limit <= 100.

### GET /transactions/{id}

Purpose: retrieve transaction detail.

Authentication: required.

Response: transaction with merchant, category, tags, import metadata.

Errors: `404` if missing or owned by another user.

### PATCH /transactions/{id}

Purpose: update user-editable fields.

Authentication: required.

Request: `{ "merchant_id": "uuid", "category_id": "uuid", "notes": "string", "tag_ids": ["uuid"] }`

Response: updated transaction.

Validation: referenced objects must belong to user.

### DELETE /transactions/{id}

Purpose: soft-delete a transaction.

Authentication: required.

Response: `{ "data": { "deleted": true } }`

## Imports

### POST /imports

Purpose: create import metadata after local parsing; raw file is not uploaded.

Authentication: required.

Request: `{ "source_type": "csv", "bank_code": "string", "file_fingerprint": "string", "privacy_mode": "maximum_privacy" }`

Response: import record.

### POST /imports/{id}/transactions

Purpose: store normalized transactions for an import.

Authentication: required.

Request: `{ "transactions": [{ "posted_date": "date", "description": "string", "sanitized_description": "string", "amount": 1.23, "direction": "debit", "dedupe_key": "string" }] }`

Response: `{ "data": { "imported_count": 100, "duplicate_count": 3, "error_count": 0 } }`

Validation: sanitized descriptions only; max batch size 500.

### GET /imports/{id}

Purpose: retrieve import summary.

Authentication: required.

Response: import status, counts, detected bank, privacy outcome.

## Merchants

### GET /merchants

Purpose: list canonical merchants.

Authentication: required.

Query: `search`, `limit`, `cursor`.

Response: paginated merchant list.

### POST /merchants

Purpose: create merchant.

Authentication: required.

Request: `{ "name": "string", "category_id": "uuid" }`

Response: merchant.

### PATCH /merchants/{id}

Purpose: update merchant name/default category.

Authentication: required.

Request: `{ "name": "string", "category_id": "uuid" }`

Response: merchant.

## Categories

### GET /categories

Purpose: list categories.

Authentication: required.

Response: system and user categories.

### POST /categories

Purpose: create custom category.

Request: `{ "name": "string", "parent_id": "uuid", "color_token": "string", "icon_name": "string" }`

Response: category.

## Rules

### GET /rules

Purpose: list deterministic rules.

Authentication: required.

Response: ordered rules.

### POST /rules

Purpose: create rule.

Request: `{ "name": "string", "priority": 10, "field": "description", "operator": "contains", "value": "string", "category_id": "uuid" }`

Response: rule.

### PATCH /rules/{id}

Purpose: update rule.

Response: rule.

### DELETE /rules/{id}

Purpose: soft-delete rule.

Response: `{ "data": { "deleted": true } }`

## Analytics

### GET /analytics/summary

Purpose: dashboard summary.

Query: `from_date`, `to_date`.

Response: totals, category breakdown, merchant breakdown, trend points.

### GET /analytics/cash-flow

Purpose: income/expense time series.

Query: `period`, `from_date`, `to_date`.

Response: time series buckets.

## AI

### POST /ai/conversations

Purpose: start AI chat session.

Request: `{ "title": "string", "context_scope": "last_90_days" }`

Response: conversation.

### POST /ai/conversations/{id}/messages

Purpose: ask AI a question using sanitized context.

Request: `{ "message": "string", "context_filters": { "from_date": "date", "to_date": "date" } }`

Response: `{ "data": { "answer": "string", "confidence": 0.82, "used_context": { "transaction_count": 120, "redactions": 4 } } }`

Errors: `403 ai_disabled`, `422 unsafe_prompt`, `429 rate_limited`.

## Settings

### GET /settings

Purpose: retrieve settings.

Response: settings key/value map.

### PATCH /settings

Purpose: update settings.

Request: `{ "privacy_mode": "maximum_privacy", "ai_enabled": false, "theme": "system" }`

Response: updated settings.
