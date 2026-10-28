"""A minimal cache interface, so endpoints don't depend on Redis directly (and tests can swap it)."""

from functools import lru_cache
from typing import Protocol

from redis import Redis

from app.core.config import get_settings


class Cache(Protocol):
    def get(self, key: str) -> bytes | None: ...

    def set(self, key: str, value: bytes, ttl_seconds: int) -> None: ...


class RedisCache:
    def __init__(self, client: Redis) -> None:
        self._client = client

    def get(self, key: str) -> bytes | None:
        return self._client.get(key)

    def set(self, key: str, value: bytes, ttl_seconds: int) -> None:
        self._client.set(key, value, ex=ttl_seconds)


@lru_cache
def get_cache() -> Cache:
    """FastAPI dependency; one connection pool per process."""
    return RedisCache(Redis.from_url(get_settings().redis_url))
