"""
NORAY — Redis Caching Service
Provides high-performance compressed caching with fallback to in-memory storage for offline capability.
"""

from __future__ import annotations
import os
import json
import zlib
import logging
from typing import Any, Optional

logger = logging.getLogger("noray.cache")


class RedisCache:
    """Redis-backed Cache with support for namespace, TTL, compression and offline fallback."""
    
    def __init__(self, namespace: str = "noray", host: str = "localhost", port: int = 6379, db: int = 0):
        self.namespace = namespace
        self.host = host
        self.port = port
        self.db = db
        self.client = None
        self._fallback_cache: dict[str, Any] = {}
        self.metrics = {"hits": 0, "misses": 0, "errors": 0}
        self._connect()

    def _connect(self):
        try:
            import redis
            r_host = os.getenv("REDIS_HOST", self.host)
            r_port = int(os.getenv("REDIS_PORT", str(self.port)))
            self.client = redis.Redis(host=r_host, port=r_port, db=self.db, socket_timeout=2)
            # test ping
            self.client.ping()
            logger.info(f"Connected to Redis cache on {r_host}:{r_port}")
        except Exception as e:
            self.client = None
            logger.warning(f"Redis cache connection failed: {e}. Falling back to in-memory cache.")

    def _get_key(self, key: str) -> str:
        return f"{self.namespace}:{key}"

    def get(self, key: str) -> Optional[Any]:
        full_key = self._get_key(key)
        if self.client:
            try:
                data = self.client.get(full_key)
                if data is None:
                    self.metrics["misses"] += 1
                    return None
                
                # Decompress
                try:
                    decompressed = zlib.decompress(data).decode('utf-8')
                    value = json.loads(decompressed)
                except Exception:
                    value = json.loads(data.decode('utf-8'))
                
                self.metrics["hits"] += 1
                return value
            except Exception as e:
                self.metrics["errors"] += 1
                logger.error(f"Redis get error: {e}")
        
        # Fallback
        if key in self._fallback_cache:
            self.metrics["hits"] += 1
            return self._fallback_cache[key]
        
        self.metrics["misses"] += 1
        return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        full_key = self._get_key(key)
        serialized = json.dumps(value)
        compressed = zlib.compress(serialized.encode('utf-8'))
        
        if self.client:
            try:
                self.client.set(full_key, compressed, ex=ttl)
                return True
            except Exception as e:
                self.metrics["errors"] += 1
                logger.error(f"Redis set error: {e}")
        
        self._fallback_cache[key] = value
        return True

    def delete(self, key: str) -> bool:
        full_key = self._get_key(key)
        if self.client:
            try:
                self.client.delete(full_key)
                return True
            except Exception as e:
                self.metrics["errors"] += 1
                logger.error(f"Redis delete error: {e}")
        
        if key in self._fallback_cache:
            del self._fallback_cache[key]
        return True

    def clear_namespace(self) -> bool:
        if self.client:
            try:
                keys = self.client.keys(f"{self.namespace}:*")
                if keys:
                    self.client.delete(*keys)
                return True
            except Exception as e:
                self.metrics["errors"] += 1
                logger.error(f"Redis clear error: {e}")
        self._fallback_cache.clear()
        return True

    def get_metrics(self) -> dict:
        return self.metrics
