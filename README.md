# Sports Calendar

[![Backend](https://github.com/fjtorresn/sports-calendar/actions/workflows/backend.yml/badge.svg)](https://github.com/fjtorresn/sports-calendar/actions/workflows/backend.yml)
[![Frontend](https://github.com/fjtorresn/sports-calendar/actions/workflows/frontend.yml/badge.svg)](https://github.com/fjtorresn/sports-calendar/actions/workflows/frontend.yml)

Un calendario deportivo personalizado. Cada usuario define **suscripciones**, como
*Fútbol – FC Barcelona – Champions League* o *F1 – solo clasificación y carrera*,
y obtiene un calendario con todos los eventos que coinciden, en la web o directamente
en **Google Calendar / Apple Calendar** mediante un feed iCal privado.

> 🚧 En desarrollo. MVP: fútbol + Fórmula 1.

## Diseño

Las decisiones del proyecto están documentadas antes del código:

- 📐 [Documento de diseño](docs/design.md): requisitos, fuentes de datos, modelo de datos,
  arquitectura, estimación de carga y plan por fases.
- 📝 [ADRs](docs/adr/): una página por decisión de arquitectura, con sus alternativas y consecuencias.

```
Web / Mobile ──► API (FastAPI) ──► PostgreSQL
Google/Apple ──► feed .ics  │  ▲
                            ▼  │ upsert
                          Redis ◄── Workers (Celery) ──► APIs deportivas / scrapers
```

## Stack

| Capa | Tecnología |
|---|---|
| API | Python 3.13 · FastAPI · SQLAlchemy 2 · Alembic · Pydantic |
| Ingesta | Celery + Redis · httpx |
| Base de datos | PostgreSQL 17 |
| Web | Next.js · TypeScript · Turborepo |
| Calidad | uv · Ruff · pytest · pre-commit · GitHub Actions |

## Estructura

```
.
├── backend/             # API, modelos, migraciones e ingesta (Python)
│   ├── src/app/
│   │   ├── api/         # Endpoints HTTP (versionados en /api/v1)
│   │   ├── core/        # Configuración y base de datos
│   │   ├── models/      # Modelos SQLAlchemy
│   │   ├── schemas/     # Esquemas Pydantic (contrato de la API)
│   │   └── workers/     # Celery y adaptadores de fuentes de datos
│   ├── alembic/         # Migraciones
│   └── tests/
├── frontend/            # Turborepo: apps/web y paquetes compartidos
├── docs/                # Diseño y ADRs
└── docker-compose.yml   # Entorno local completo
```

## Desarrollo local

**Requisitos:** Docker, [uv](https://docs.astral.sh/uv/) y Node 22.

```bash
cp .env.example .env          # configuración local
docker compose up --build     # API en http://localhost:8000/docs
```

**Backend sin Docker** (usando solo `db` y `redis` de Docker):

```bash
docker compose up -d db redis
cd backend
uv sync                        # instala Python 3.13 y las dependencias
uv run alembic upgrade head    # aplica las migraciones
uv run uvicorn app.api.main:app --reload
```

**Calidad:**

```bash
cd backend
uv run pytest                  # tests (necesitan el PostgreSQL de Docker)
uv run ruff check . && uv run ruff format --check .
uv run pre-commit install      # ejecuta los checks en cada commit
```

**Frontend:**

```bash
cd frontend && npm install && npm run dev
```

## Estado

| Fase | Estado |
|---|---|
| 0. Base (CI, configuración, entorno local) | 🔄 En curso |
| 1. Diseño | ✅ |
| 2. Modelo de datos v2 | ⏳ |
| 3. Ingesta (football-data.org, Jolpica F1) | ⏳ |
| 4. Usuarios, suscripciones, calendario y feed iCal | ⏳ |
| 5. Web | ⏳ |
| 6. Despliegue | ⏳ |
