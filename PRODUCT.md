# Tally Product Specification

## Vision

Tally helps people understand their money from bank statements without giving up control of sensitive financial data. It turns imported statements into clean transaction history, useful analytics, and privacy-preserving AI insights.

## Goals

- Make statement import trustworthy and understandable.
- Keep raw bank statements out of long-term storage by default.
- Provide clear spending, income, merchant, and category insights.
- Offer AI explanations without exposing banking identifiers or raw files.
- Work well on mobile and remain useful offline.

## Features

- Account signup, login, logout, and password reset.
- CSV import with bank detection and import preview.
- Transaction normalization and duplicate detection.
- Merchant aliasing and category rules.
- Transaction timeline, filters, search, tags, and details.
- Dashboard analytics for current period and historical trends.
- AI chat using sanitized financial context.
- Privacy modes: Maximum Privacy, Cloud Sync, Archive.
- Settings for theme, sync, import behavior, AI, and account.

## Target Users

- Students tracking monthly spending.
- Professionals monitoring salary, bills, and subscriptions.
- Families reviewing household expenses.
- Freelancers separating personal and work-related cash flow.

## Competitive Advantages

- Deletes raw statements by default.
- AI cannot access raw statements or sensitive identifiers.
- Supports offline viewing and local-first workflows.
- Gives users explicit privacy modes instead of hidden defaults.
- Uses deterministic financial rules before AI suggestions.
- Designed for future multi-bank and PDF support.

## User Stories

- As a user, I want to import a CSV statement so I can see transactions without manual entry.
- As a privacy-conscious user, I want the original statement deleted after import so my sensitive file does not linger.
- As a user, I want duplicate detection so repeated imports do not pollute my history.
- As a user, I want merchant names cleaned up so my spending is easier to understand.
- As a user, I want dashboard summaries so I can quickly understand where my money went.
- As a user, I want to ask AI questions about spending without exposing account numbers or raw statements.
- As a user, I want to change privacy mode so I control whether data syncs or files are archived.
- As a freelancer, I want tags so I can mark business expenses.

## Future Roadmap

- PDF imports.
- Budget creation and tracking.
- Recurring transaction detection.
- Subscription alerts.
- Family/shared accounts.
- Export to CSV/XLSX.
- More AI providers and local AI options.
- Web client.
- On-device merchant/category models.

## Success Metrics

- Import success rate by bank format.
- Duplicate detection accuracy.
- Percentage of raw files deleted after successful import.
- Dashboard load time.
- User retention after first successful import.
- AI answer helpfulness rating.
- Number of privacy violations found in automated prompt tests: target zero.
- Support tickets related to incorrect transactions or confusing imports.
