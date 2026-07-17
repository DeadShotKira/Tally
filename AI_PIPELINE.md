# AI Pipeline

## Goals

AI helps with merchant resolution, categorization, summaries, anomaly explanations, and chat. It never receives raw statements or sensitive banking identifiers.

## Merchant Resolution

Resolution order:

1. User-confirmed merchant aliases.
2. Deterministic rules.
3. Merchant memory from prior corrections.
4. Local normalization heuristics.
5. AI suggestion using sanitized description only.
6. Unknown merchant flow.

## Rule Engine

Rules are deterministic and ordered by priority. They can match sanitized description, amount range, direction, existing merchant, category, or tags. Rules are explainable and override AI.

## Merchant Memory

When a user corrects a merchant or category, Tally stores an alias or rule candidate. Future imports apply that memory automatically after confirmation rules.

## Unknown Merchant Flow

Unknown merchants are shown in a review queue. The user can accept an AI suggestion, choose an existing merchant, create a new merchant, ignore, or create a rule.

## Categorization

Categorization follows the same precedence: explicit rules, merchant default category, memory, AI suggestion, fallback category.

## AI Chat

AI chat answers questions over sanitized, scoped financial context. The chat cannot query raw database rows directly; it receives a generated context package from the privacy engine.

## Prompt Construction

Prompt inputs:

- System policy with privacy boundaries.
- User question after sensitive-data filtering.
- Aggregated summaries when possible.
- Sanitized transaction snippets only when needed.
- Synthetic transaction IDs.
- Time range and filter metadata.

## Privacy Filtering

Before any AI request:

- Raw files are unavailable.
- Statement headers are dropped.
- Sensitive patterns are redacted.
- Descriptions are replaced with sanitized descriptions.
- Account-like identifiers are removed.
- Context size is minimized.

## Context Generation

The context generator prefers aggregates over individual transactions. If individual transactions are required, it includes date, amount, direction, category, merchant, tags, and sanitized description.

## Confidence Scoring

AI responses include confidence where applicable. Low-confidence merchant/category suggestions require user confirmation and are not auto-applied.

## Fallback Behavior

If AI is disabled, unavailable, unsafe, or low-confidence, Tally falls back to deterministic rules, local analytics, and user review queues.

## Caching

AI suggestions may be cached by sanitized input hash, user, and model version. Cached data must not contain sensitive identifiers.

## Sensitive Data Prevention

AI is prevented from accessing sensitive data through layered controls:

- No raw-file API path.
- Sanitized context builder.
- Sensitive-pattern detector.
- Prompt regression tests.
- Backend allowlist of AI context fields.
- Logging redaction.
- Runtime rejection if unsafe patterns remain.
