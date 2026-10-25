# Sports Calendar

[![CI](https://github.com/fjtorresn/sports-calendar/actions/workflows/ci.yml/badge.svg)](https://github.com/fjtorresn/sports-calendar/actions/workflows/ci.yml)

A personalized sports calendar. Each user defines **subscriptions**, such as
*Football – FC Barcelona – Champions League* or *F1 – qualifying and race only*,
and gets a calendar with every matching event, on the web or directly in
**Google Calendar / Apple Calendar** through a private iCal feed.

> 🚧 Work in progress. MVP: football + Formula 1.

## Design

The project's decisions are documented before the code:

- 📐 [Design document](docs/design.md): requirements, data sources, data model,
  architecture, load estimate and phased plan.
- 📝 [ADRs](docs/adr/): one page per architecture decision, with its alternatives and consequences.

```
Web / Mobile ──► API (FastAPI) ──► PostgreSQL
Google/Apple ──► .ics feed  │  ▲
                            ▼  │ upsert
                          Redis ◄── Workers (Celery) ──► sports APIs / scrapers
```

## Stack

| Layer | Technology |
|---|---|
| API | Python 3.13 · FastAPI · SQLAlchemy 2 · Alembic · Pydantic |
| Ingestion | Celery + Redis · httpx |
| Database | PostgreSQL 17 |
| Web | Next.js · TypeScript · Turborepo |
| Quality | uv · Ruff · pytest · pre-commit · GitHub Actions |

## Layout

```
.
├── backend/             # API, models, migrations and ingestion (Python)
│   ├── src/app/
│   │   ├── api/         # HTTP endpoints (versioned under /api/v1)
│   │   ├── core/        # Settings and database
│   │   ├── models/      # SQLAlchemy models
│   │   ├── schemas/     # Pydantic schemas (the API contract)
│   │   └── workers/     # Celery and data source adapters
│   ├── alembic/         # Migrations
│   └── tests/
├── frontend/            # Turborepo: apps/web and shared packages
├── docs/                # Design and ADRs
└── docker-compose.yml   # Full local environment
```

## Local development

**Requirements:** Docker, [uv](https://docs.astral.sh/uv/) and Node 22.

```bash
cp .env.example .env          # local settings
docker compose up --build     # API at http://localhost:8000/docs
```

**Backend without Docker** (using only `db` and `redis` from Docker):

```bash
docker compose up -d db redis
cd backend
uv sync                        # installs Python 3.13 and the dependencies
uv run alembic upgrade head    # applies migrations
uv run uvicorn app.api.main:app --reload
```

**Quality checks:**

```bash
cd backend
uv run pytest                  # tests (need the PostgreSQL container)
uv run ruff check . && uv run ruff format --check .
uv run pre-commit install      # run the checks on every commit
```

**Frontend:**

```bash
cd frontend && npm install && npm run dev
```

## Status

| Phase | Status |
|---|---|
| 0. Foundation (CI, settings, local environment) | 🔄 In progress |
| 1. Design | ✅ |
| 2. Data model v2 | ⏳ |
| 3. Ingestion (football-data.org, Jolpica F1) | ⏳ |
| 4. Users, subscriptions, calendar and iCal feed | ⏳ |
| 5. Web | ⏳ |
| 6. Deployment | ⏳ |
