"""A lightweight Redis-like client used for tests or offline environments."""
from __future__ import annotations

import threading
import time
from typing import Optional


class _InMemoryLock:
    def __init__(self, backend: "InMemoryRedis", name: str, timeout: Optional[int], blocking_timeout: Optional[int]):
        self._backend = backend
        self._name = name
        self._timeout = timeout
        self._blocking_timeout = blocking_timeout
        self._local_lock: Optional[threading.Lock] = None

    def acquire(self, blocking: bool = True) -> bool:
        start = time.time()
        while True:
            with self._backend._mutex:
                lock = self._backend._locks.get(self._name)
                if lock is None or not lock.locked():
                    lock = threading.Lock()
                    lock.acquire()
                    self._backend._locks[self._name] = lock
                    self._local_lock = lock
                    return True
            if not blocking:
                return False
            if self._blocking_timeout is not None and time.time() - start >= self._blocking_timeout:
                return False
            time.sleep(0.05)

    def release(self) -> None:
        with self._backend._mutex:
            if self._local_lock and self._local_lock.locked():
                self._local_lock.release()
                self._backend._locks.pop(self._name, None)
                self._local_lock = None

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.release()


class InMemoryRedis:
    def __init__(self):
        self._data: dict[str, str] = {}
        self._expirations: dict[str, float] = {}
        self._locks: dict[str, threading.Lock] = {}
        self._mutex = threading.Lock()

    def _purge(self, key: str) -> None:
        expire_at = self._expirations.get(key)
        if expire_at is not None and expire_at <= time.time():
            self._data.pop(key, None)
            self._expirations.pop(key, None)

    def get(self, key: str) -> Optional[str]:
        with self._mutex:
            self._purge(key)
            return self._data.get(key)

    def setex(self, key: str, ttl: int, value: str) -> None:
        with self._mutex:
            self._data[key] = value
            self._expirations[key] = time.time() + ttl

    def delete(self, key: str) -> None:
        with self._mutex:
            self._data.pop(key, None)
            self._expirations.pop(key, None)

    def lock(self, name: str, timeout: Optional[int] = None, blocking_timeout: Optional[int] = None):
        return _InMemoryLock(self, name, timeout, blocking_timeout)

    # Compatibility helpers
    def ping(self) -> bool:
        return True
