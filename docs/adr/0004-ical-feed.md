# 0004 — iCal feed with a private token and TTL caching

- **Status:** Accepted
- **Date:** 2026-10-21

## Context

Users want to see their events in Google Calendar or Apple Calendar. Those clients
subscribe to an `.ics` URL (RFC 5545) and poll it periodically, **without** sending
credentials.

## Decision

- Each user has a random `ical_token` (≥ 32 bytes, `secrets.token_urlsafe`), unique and
  revocable. URL: `GET /calendar/{ical_token}.ics`.
- Each event has a stable `UID` (derived from `events.id`), so a time change **updates**
  the event in the calendar instead of duplicating it.
- Times in UTC; `date_only` events are published as all-day events.
- The response is cached in Redis with a **1-hour TTL**, without explicit invalidation.
- The feed is built in the same phase as the web calendar, since both use the same query.

## Consequences

- ✅ Works with any calendar client, no dedicated app required.
- ✅ Low cost per request; the cache absorbs repeated polling.
- ⚠️ The URL **is** the credential: if it leaks, anyone can see the calendar (which holds
  no sensitive data). Mitigation: the token can be regenerated.
- ⚠️ Total delay = daily sync + TTL + client refresh interval (Google: up to ~24 h).
  Acceptable per NFR-1; if it isn't enough, the answer is push notifications, not a
  shorter TTL.
