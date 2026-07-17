# Security Design

## Threat Model

Assets: user identity, tokens, normalized transaction data, archived files, encryption keys, AI context, database records.

Attackers: malicious local files, compromised network, unauthorized users, prompt injection attempts, cross-tenant access attempts, leaked logs, compromised device.

## Authentication Risks

- Stolen tokens: store only in Secure Storage, use short-lived access tokens, support logout.
- Invalid JWTs: verify signature, issuer, audience, expiration.
- Account takeover: rely on Supabase password reset and future MFA support.

## SQL Injection

Use SQLAlchemy parameterized queries. Never concatenate user input into SQL. Validate filters and sort fields against allowlists.

## Prompt Injection

Transaction descriptions can contain malicious instructions. AI prompts must treat transaction text as untrusted data, use structured context, and include no raw file content.

## File Upload Security

Initial design avoids backend raw file upload. Local file handling copies into app-controlled temporary storage, validates size/type, and deletes after use.

## CSV Attacks

Risks include formula injection, malformed encodings, oversized files, hidden delimiters, and malicious text. Mitigations include size limits, strict parsers, formula neutralization on export, row limits, and safe preview rendering.

## PDF Attacks

Future PDF import must sandbox parsing, limit file size/page count, avoid executing embedded content, and treat extracted text as untrusted.

## Rate Limiting

Apply per-user and per-IP limits for auth-sensitive endpoints, AI endpoints, imports, and search. AI endpoints need stricter quotas.

## Encryption

- In transit: HTTPS.
- Tokens/keys: Secure Storage.
- Archive Mode files: app-managed encryption.
- Database: Supabase managed encryption at rest.

## Secrets Management

Backend secrets live in environment variables or managed secret storage. Service role keys never ship to the mobile app.

## RLS Strategy

Every user-owned table enforces `user_id = auth.uid()` mapping directly or through backend-controlled access. Backend queries also scope by authenticated user.

## Audit Logging

Log security-relevant events: login bootstrap, import completion, privacy mode changes, archive creation/deletion, AI request metadata, and suspicious validation failures. Logs must exclude sensitive values.

## Secure Storage

Secure Storage contains access tokens, refresh tokens, device ID, and archive keys. Hive must not contain secrets.
