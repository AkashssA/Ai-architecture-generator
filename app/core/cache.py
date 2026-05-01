import asyncio
import json
import time
from typing import Any, Optional

try:
    from redis.asyncio import Redis, from_url as redis_from_url
except ImportError:  # pragma: no cover
    Redis = None
    redis_from_url = None


class CacheBackend:
    async def get(self, key: str) -> Optional[dict[str, Any]]:
        raise NotImplementedError

    async def set(self, key: str, value: dict[str, Any], ttl_seconds: int) -> None:
        raise NotImplementedError

    async def close(self) -> None:
        return None


class InMemoryCache(CacheBackend):
    def __init__(self) -> None:
        self._store: dict[str, tuple[float, dict[str, Any]]] = {}
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Optional[dict[str, Any]]:
        async with self._lock:
            record = self._store.get(key)
            if not record:
                return None

            expires_at, value = record
            if expires_at < time.time():
                self._store.pop(key, None)
                return None

            return value

    async def set(self, key: str, value: dict[str, Any], ttl_seconds: int) -> None:
        async with self._lock:
            self._store[key] = (time.time() + ttl_seconds, value)


class RedisCache(CacheBackend):
    def __init__(self, redis: Redis) -> None:
        self._redis = redis

    async def get(self, key: str) -> Optional[dict[str, Any]]:
        payload = await self._redis.get(key)
        if not payload:
            return None
        return json.loads(payload)

    async def set(self, key: str, value: dict[str, Any], ttl_seconds: int) -> None:
        await self._redis.set(key, json.dumps(value), ex=ttl_seconds)

    async def close(self) -> None:
        await self._redis.close()


async def build_cache(redis_url: Optional[str]) -> CacheBackend:
    if redis_url and redis_from_url:
        redis = redis_from_url(redis_url, decode_responses=True)
        return RedisCache(redis)
    return InMemoryCache()
