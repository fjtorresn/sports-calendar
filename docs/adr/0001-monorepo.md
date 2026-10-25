# 0001 — Monorepo for backend, web and mobile

- **Status:** Accepted
- **Date:** 2026-10-21

## Context

The project started as two repositories (`sports-calendar-backend` and
`sports-calendar-frontend`). The plan includes a web app and a mobile app, both
consuming the same API. Development is done by a single person.

## Decision

A single `sports-calendar` repository with `backend/` (Python) and `frontend/`
(Turborepo: `apps/web`, `apps/mobile`, `packages/*`). The original repositories were
imported with `git subtree add`, preserving their history.

## Consequences

- ✅ A change to the API and to its clients lands in a single commit or PR.
- ✅ `packages/api-client`, generated from FastAPI's OpenAPI schema, is shared by web
  and mobile; if the contract changes, TypeScript fails to compile.
- ✅ A single portfolio link shows the whole system.
- ⚠️ CI needs path filters so Python tests don't run when only the frontend changes,
  and vice versa.
- ⚠️ Imported commits keep their original paths; to follow a file across the
  migration, use `git log --follow`.
- Repository structure **does not affect** runtime scale: each component is deployed
  independently.
