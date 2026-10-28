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

### Try it locally (MVP)

```bash
cp .env.example .env               # then set FOOTBALL_DATA_API_KEY (free at football-data.org)
docker compose up -d --build
cd backend
uv run python -m app.scripts.seed            # catalog: football (13 competitions) + F1
uv run python -m app.scripts.sync --all      # real data from football-data.org and Jolpica
uv run python -m app.scripts.user create --email me@example.com --timezone America/Santiago
uv run python -m app.scripts.user follow --email me@example.com --competitor Barcelona
uv run python -m app.scripts.user follow --email me@example.com --sport formula-1 --kinds qualifying,sprint,race
uv run python -m app.scripts.user list --email me@example.com   # prints your iCal URL
```

Open the iCal URL in a calendar app that can reach `localhost` (GNOME Calendar,
Thunderbird, Apple Calendar on the same machine), or save it with `curl` and import the
file into Google Calendar. Subscribing from Google Calendar or a phone needs a public
URL, which comes with deployment.

**Backend without Docker** (using only `db` and `redis` from Docker):

```bash
docker compose up -d db redis
cd backend
uv sync                        # installs Python 3.13 and the dependencies
uv run alembic upgrade head    # applies migrations
uv run python -m app.scripts.seed  # loads the MVP catalog (idempotent)
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
| 0. Foundation (CI, settings, local environment) | ✅ |
| 1. Design | ✅ |
| 2. Data model v2 and core calendar query | ✅ |
| MVP: ingestion, CLI subscriptions, iCal feed | 🔄 In progress |
| 3. Ingestion (football-data.org, Jolpica F1) | ⏳ |
| 4. Users, subscriptions, calendar and iCal feed | ⏳ |
| 5. Web | ⏳ |
| 6. Deployment | ⏳ |
