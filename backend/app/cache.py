import time
from threading import Lock

_DASHBOARD_CACHE = {}
_DASHBOARD_LOCKS = {}

# 可調整 TTL（秒）
CACHE_TTL_SECONDS = 90


def get_dashboard_cache(user_id: int):
    entry = _DASHBOARD_CACHE.get(user_id)
    if not entry:
        return None
    payload, ts = entry
    if time.time() - ts > CACHE_TTL_SECONDS:
        return None
    return payload


def set_dashboard_cache(user_id: int, payload):
    _DASHBOARD_CACHE[user_id] = (payload, time.time())


def clear_dashboard_cache(user_id: int):
    _DASHBOARD_CACHE.pop(user_id, None)


def get_user_lock(user_id: int) -> Lock:
    lock = _DASHBOARD_LOCKS.get(user_id)
    if lock is None:
        lock = Lock()
        _DASHBOARD_LOCKS[user_id] = lock
    return lock
