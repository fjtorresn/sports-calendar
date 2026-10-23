FROM python:3.13-slim

# uv se copia desde su imagen oficial (versión fijada para builds reproducibles).
COPY --from=ghcr.io/astral-sh/uv:0.13 /uv /uvx /bin/

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

# 1) Solo dependencias: esta capa se reutiliza mientras pyproject.toml/uv.lock no cambien.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# 2) El código del proyecto.
COPY . .
RUN uv sync --frozen --no-dev

# No correr como root dentro del contenedor.
RUN useradd --create-home --uid 1000 appuser
USER appuser

EXPOSE 8000
CMD ["uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
