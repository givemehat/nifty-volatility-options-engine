"""
Lightweight in-memory TTL Cache for FastAPI read endpoints.
"""

import time
from functools import wraps
from typing import Dict, Any, Tuple, Callable, Optional

class TTLCache:
    def __init__(self, default_ttl: int = 60):
        self._cache: Dict[str, Tuple[float, Any]] = {}
        self.default_ttl = default_ttl

    def get(self, key: str) -> Optional[Any]:
        if key in self._cache:
            exp_time, val = self._cache[key]
            if time.time() < exp_time:
                return val
            else:
                del self._cache[key]
        return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        duration = ttl if ttl is not None else self.default_ttl
        self._cache[key] = (time.time() + duration, value)

    def clear(self) -> None:
        self._cache.clear()

memory_cache = TTLCache(default_ttl=60)
