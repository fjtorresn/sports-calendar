# CLAUDE.md

Guide for working on this repository with Claude Code.

## Context

- This is a portfolio and learning project. **Explain decisions** (what, why, and which
  alternatives were considered) before and during implementation, not just the code.
- **Language:** everything in the repository is in **English**: code, identifiers,
  comments, docstrings, log messages, docs, ADRs, commit messages and PR descriptions.
  Conversation with the user is in **Spanish**.
- Before design changes, read [docs/design.md](docs/design.md) and the ADRs in
  [docs/adr/](docs/adr/). If a decision changes, write a new ADR that supersedes the
  old one; accepted ADRs are never rewritten.
- Requirements have IDs (`FR-n`, `NFR-n`, design.md §2): reference them in PRs and tests.

## Layout

- `backend/`: Python 3.13 managed with **uv**. The package is `app` (src layout:
  `backend/src/app`), imported as `from app.x import y`, never `src.app`.
- `frontend/`: Turborepo with npm workspaces (`apps/web`, `packages/*`).
- Docker Compose lives at the root; settings live in `.env` (copied from `.env.example`).

## Commands (backend, from `backend/`)

```bash
uv sync                              # install dependencies
uv run pytest                        # tests (requires: docker compose up -d db)
uv run ruff check . --fix && uv run ruff format .
uv run alembic revision --autogenerate -m "message"
uv run alembic upgrade head
uv run alembic check                # models and migrations must not drift
uv run python -m app.scripts.seed    # idempotent MVP catalog
```

## Conventions

- **Branches:** `feat/…`, `fix/…`, `chore/…`, `docs/…`. Never commit directly to `main`;
  everything goes through a PR.
- **Commits:** [Conventional Commits](https://www.conventionalcommits.org/)
  (`feat: add iCal endpoint`). Small commits, one purpose each.
- **Comments** explain *why*, not *what*; don't restate the code.
- **Settings:** any value that varies between environments or is secret goes in
  `app.core.config.Settings`, read from the environment. No URLs or passwords in code.
- **Database:** every model change ships with its Alembic migration. Tests run against
  a **real PostgreSQL**, never SQLite.
- **Models:** register every new model in `app/models/__init__.py`. Fixed-value columns are
  `StrEnum`s mapped with `string_enum()` (ADR 0005); changing their values needs a
  hand-written migration, since `alembic check` can't see it.
- **Tests:** use the `db` fixture (rolled back after each test) and `tests/factories.py`.
  Warnings are errors.
- **Dependencies:** add them with `uv add` (or `uv add --dev`); commit `uv.lock`.
- **Data sources:** each source is an `EventProvider` adapter (ADR 0002); the rest of
  the system knows nothing about source details.
