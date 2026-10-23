# CLAUDE.md

Guía para trabajar en este repo con Claude Code.

## Contexto

- Proyecto de portafolio y de aprendizaje. **Explicar las decisiones** (qué, por qué y
  qué alternativas hubo) antes y durante la implementación, no solo escribir código.
  Responder en español.
- Antes de cambios de diseño, leer [docs/design.md](docs/design.md) y los ADRs de
  [docs/adr/](docs/adr/). Si una decisión cambia, se escribe un ADR nuevo que reemplaza
  al anterior; los ADRs aceptados no se reescriben.
- Los requisitos tienen IDs (`RF-n`, `RNF-n`, en design.md §2): citarlos en PRs y tests.

## Estructura

- `backend/`: Python 3.13 gestionado con **uv**. El paquete es `app` (src layout:
  `backend/src/app`) y los imports son `from app.x import y`, nunca `src.app`.
- `frontend/`: Turborepo con npm workspaces (`apps/web`, `packages/*`).
- Docker Compose en la raíz; la configuración vive en `.env` (copiar de `.env.example`).

## Comandos (backend, desde `backend/`)

```bash
uv sync                              # instalar dependencias
uv run pytest                        # tests (necesita: docker compose up -d db)
uv run ruff check . --fix && uv run ruff format .
uv run alembic revision --autogenerate -m "mensaje"
uv run alembic upgrade head
```

## Convenciones

- **Ramas:** `feat/…`, `fix/…`, `chore/…`, `docs/…`. Nunca commits directos a `main`; todo entra por PR.
- **Commits:** [Conventional Commits](https://www.conventionalcommits.org/) en inglés
  (`feat: add iCal endpoint`). Commits pequeños, cada uno con un propósito.
- **Configuración:** todo valor que cambie entre entornos o que sea secreto va en
  `app.core.config.Settings`, leído del entorno. Nada de URLs ni contraseñas en el código.
- **Base de datos:** cada cambio de modelo va con su migración de Alembic. Los tests
  corren contra **PostgreSQL real**, nunca SQLite.
- **Modelos:** cada modelo nuevo se registra en `app/models/__init__.py`.
- **Dependencias:** se agregan con `uv add` (o `uv add --dev`); `uv.lock` se commitea.
- **Fuentes de datos:** cada fuente es un adaptador de `EventProvider` (ADR 0002); el
  resto del sistema no conoce detalles de las fuentes.
