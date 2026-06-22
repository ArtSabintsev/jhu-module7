from __future__ import annotations

import json
import logging
from typing import Any

import redis

from inventory_reorder.settings import Settings

logger = logging.getLogger(__name__)


class InventoryCache:
    def __init__(self, redis_client: Any | None, ttl_seconds: int) -> None:
        self.redis = redis_client
        self.ttl_seconds = ttl_seconds

    @classmethod
    def from_settings(cls, settings: Settings) -> "InventoryCache":
        if not settings.redis_url:
            logger.warning("REDIS_URL is not set; cache is disabled.")
            return cls(None, settings.cache_ttl_seconds)
        client = redis.Redis.from_url(
            settings.redis_url,
            decode_responses=True,
            socket_connect_timeout=2,
            socket_timeout=2,
        )
        return cls(client, settings.cache_ttl_seconds)

    @property
    def enabled(self) -> bool:
        return self.redis is not None

    def get_json(self, key: str) -> Any | None:
        if self.redis is None:
            return None
        try:
            raw = self.redis.get(key)
        except redis.RedisError:
            logger.exception("cache read failed; falling back to source key=%s", key)
            return None
        if raw is None:
            logger.info("cache miss: %s", key)
            return None
        logger.info("cache hit: %s", key)
        return json.loads(raw)

    def set_json(self, key: str, value: Any) -> None:
        if self.redis is None:
            return
        try:
            self.redis.setex(key, self.ttl_seconds, json.dumps(value, sort_keys=True))
        except redis.RedisError:
            logger.exception("cache write failed key=%s", key)

    def delete(self, *keys: str) -> None:
        if self.redis is None or not keys:
            return
        try:
            self.redis.delete(*keys)
        except redis.RedisError:
            logger.exception("cache delete failed keys=%s", keys)
