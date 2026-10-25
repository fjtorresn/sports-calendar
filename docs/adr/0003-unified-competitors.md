# 0003 — A single `competitors` table for teams and individuals

- **Status:** Accepted
- **Date:** 2026-10-21

## Context

Model v1 had separate `teams` and `players` tables, and `event_participants` pointed
at either through `participant_type` + `participant_id`, with no foreign key. The
database could not guarantee that a participant existed, and subscriptions needed
parallel `team_id` and `player_id` columns.

## Decision

A `competitors` table with `kind = team | individual`. `event_participants.competitor_id`
and `subscriptions.competitor_id` are real foreign keys. The player ↔ team relationship
is modeled separately with a temporal `competitor_memberships` table
(`valid_from`/`valid_to`), after the MVP (design.md §4.6).

## Alternatives considered

- **Keep separate tables with optional FKs** (`team_id`, `player_id` + `CHECK`):
  preserves integrity, but every filter and query is duplicated per competitor type.
- **Table inheritance** (a base table + `teams`/`players` sharing its id): closer to the
  domain, but adds joins and ORM complexity the MVP doesn't need.

## Consequences

- ✅ Referential integrity for participants and subscriptions.
- ✅ "Follow X" works the same for Barcelona, Djokovic or Verstappen.
- ✅ Tennis doubles and driver ↔ constructor in F1 fit the membership model.
- ⚠️ Type-specific attributes (e.g. a tennis player's handedness) have no column; if
  needed, they go into a per-type detail table.
