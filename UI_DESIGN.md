# UI Design

## Global Principles

Use Flutter Material 3, mobile-first navigation, consistent spacing, accessible contrast, dark mode, and responsive layouts. Every screen defines loading, empty, and error states.

## Splash

Purpose: initialize app, load theme, check session.

Components: app mark/name, progress indicator.

Navigation: login if unauthenticated; dashboard if authenticated.

States: loading initialization; error for unrecoverable startup issue.

Accessibility: screen-reader status label.

## Login

Purpose: authenticate user.

Components: email field, password field, login button, signup link, password reset link.

Navigation: dashboard after login; signup/password reset flows as needed.

States: validation errors, network error, loading button.

Accessibility: labeled fields, visible validation text.

## Dashboard

Purpose: financial overview.

Components: period selector, income/spend summary, category chart, recent transactions, merchant highlights, import shortcut.

Navigation: transaction timeline, import, AI chat, settings.

Empty state: prompt to import first statement.

Loading: cached data first, refresh indicator.

Error: retry analytics refresh.

Responsive: two-column summary on tablets.

## Timeline

Purpose: browse transactions.

Components: search, filters, grouped transaction list, sort, tag/category chips.

Navigation: transaction detail on tap.

Empty state: no transactions or no filter results.

Loading: skeleton rows.

Error: retry list load.

## Transaction Detail

Purpose: inspect and edit one transaction.

Components: amount, date, merchant, category, tags, notes, import source, privacy-safe description.

Navigation: merchant detail, category picker, tag editor.

Actions: edit category, assign merchant, add tags, delete transaction.

Accessibility: amount direction announced clearly.

## Merchant Detail

Purpose: show merchant history and settings.

Components: merchant name, default category, aliases, spend trend, transactions.

Actions: rename merchant, merge aliases, set category, create rule.

Empty state: no additional history.

## Import Statement

Purpose: import CSV statement.

Components: file picker, bank detection result, preview table, error list, privacy mode notice, confirm button.

Navigation: summary after import.

Loading: parsing progress.

Error: unsupported bank, invalid CSV, row errors.

Accessibility: table summaries and row error counts.

## AI Chat

Purpose: ask privacy-safe questions.

Components: conversation list, message thread, input box, context scope selector, privacy indicator.

Actions: send message, change scope, clear conversation.

Empty state: suggested privacy-safe prompts.

Error: AI disabled, unsafe prompt, service unavailable.

Accessibility: messages announced by role and time.

## Settings

Purpose: manage account, privacy, sync, AI, theme.

Components: privacy mode selector, cloud sync toggle, archive controls, AI toggle, theme selector, account actions.

Actions: change mode, logout, delete account, clear cache.

Error: mode change failure, sync conflict.

Responsive: grouped settings sections on tablet.
