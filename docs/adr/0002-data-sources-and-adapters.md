# 0002 — Multiple data sources behind a common interface

- **Status:** Accepted
- **Date:** 2026-10-21

## Context

No free source covers every sport (see design.md §3.2). Free APIs have small quotas
(≈100 req/day), and some sports, such as boxing, have no reliable API at all.

## Decision

- **Free APIs** come first; **scraping** is used only when there is no API.
- Each source is implemented as an adapter of the `EventProvider` interface, which
  returns normalized DTOs. The rest of the system doesn't know where data came from.
- Identity across sources is resolved with the `*_external_refs` tables
  (`UNIQUE (source, external_id)`), which make the upsert idempotent.
- Ingestion is **on demand**: only competitions with subscribers are synced.

## Consequences

- ✅ Adding a sport or a source = a new adapter (NFR-6).
- ✅ Ingestion cost depends on the followed catalog, not on the number of users.
- ⚠️ Scrapers are brittle: they need tests with recorded HTML and alerts when they
  return 0 events.
- ⚠️ Entity resolution across sources starts out manual.
- ⚠️ If the app goes public, licensing must be reviewed: the iCal feed redistributes
  third-party data.
