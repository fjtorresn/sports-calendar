# 0005 — Fixed-value columns as VARCHAR + CHECK, not native ENUM

- **Status:** Accepted
- **Date:** 2026-10-25

## Context

Several columns only accept a fixed set of values: `events.status`, `events.time_precision`,
`competitors.kind`, the `source` of external refs and sync state. The database must reject
anything else (FR-6 depends on a reliable `status`), and the sets will grow (e.g. a `live`
status, a new data source per sport added).

## Decision

Each set is a Python `StrEnum` (`app/models/enums.py`), mapped with
`sa.Enum(..., native_enum=False, create_constraint=True)`: a `VARCHAR` column plus a named
`CHECK (col IN (...))` constraint. Values are stored as the enum *values* (`not_before`),
not member names.

## Alternatives considered

- **Native PostgreSQL `ENUM` types** (`CREATE TYPE`): compact and self-describing, but
  changing them is awkward: values can be added but not removed or renamed without
  recreating the type, and Alembic autogenerate doesn't handle those changes.
- **Lookup tables** with FKs: maximally flexible, but adds a join for values that only
  change together with the code that handles them.

## Consequences

- ✅ Invalid values are rejected by the database, not just by the API.
- ✅ Changing a set is a plain `DROP CONSTRAINT` / `ADD CONSTRAINT` migration; the
  naming convention makes constraint names predictable (`ck_events_eventstatus`).
- ⚠️ `alembic check` does **not** detect a changed value list: adding an enum member
  requires a hand-written migration. A test that writes the new value catches a missing one.
- ⚠️ Slightly larger storage than a native enum; irrelevant at our scale (design.md §6).
