"""Configuración de la aplicación.

Los valores se leen de variables de entorno (y de un archivo ``.env`` en desarrollo).
No hay valores por defecto para secretos: si falta uno, la app falla al arrancar en vez
de conectarse a algo inesperado.
"""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        # El .env vive en la raíz del monorepo; también se busca en el directorio actual.
        env_file=("../.env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    environment: Literal["development", "test", "production"] = "development"
    database_url: str
    redis_url: str


@lru_cache
def get_settings() -> Settings:
    """Devuelve la configuración, leída una sola vez por proceso."""
    return Settings()
