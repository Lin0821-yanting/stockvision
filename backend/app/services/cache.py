"""記憶體 TTL 快取。

同一個 key 同時有多個請求時只會呼叫一次外部 API（其他請求等待同一份結果），
可以減少 FinMind 每小時額度與 MIS 頻率限制的消耗。
"""

from __future__ import annotations

import asyncio
import time
from collections.abc import Awaitable, Callable
from typing import Any, TypeVar

T = TypeVar("T")
_MISSING = object()


class TTLCache:
    def __init__(self) -> None:
        self._data: dict[str, tuple[float, Any]] = {}
        self._locks: dict[str, asyncio.Lock] = {}

    def get(self, key: str, default: Any = None) -> Any:
        item = self._data.get(key)
        if item is None:
            return default
        expires_at, value = item
        if expires_at < time.monotonic():
            self._data.pop(key, None)
            return default
        return value

    def set(self, key: str, value: Any, ttl: float) -> None:
        self._data[key] = (time.monotonic() + ttl, value)

    def lock(self, name: str) -> asyncio.Lock:
        return self._locks.setdefault(name, asyncio.Lock())

    async def get_or_set(self, key: str, ttl: float, factory: Callable[[], Awaitable[T]]) -> T:
        value = self.get(key, _MISSING)
        if value is not _MISSING:
            return value
        async with self.lock(f"key:{key}"):
            value = self.get(key, _MISSING)
            if value is not _MISSING:
                return value
            value = await factory()
            self.set(key, value, ttl)
            return value

    def clear(self) -> None:
        self._data.clear()
        self._locks.clear()


cache = TTLCache()
