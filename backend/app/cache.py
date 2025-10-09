import json
from typing import Any, Optional

from flask import current_app

# 可調整 TTL（秒）
CACHE_TTL_SECONDS = 90
BI_CACHE_TTL_SECONDS = 120
BI_RATE_LIMIT_PER_MINUTE = 20
_BI_RATE_WINDOW_SECONDS = 60

_CACHE_KEY = "dashboard-cache:{user_id}"
_LOCK_KEY = "dashboard-lock:{user_id}"
_BI_CACHE_KEY = "bi-cache:{user_id}:{endpoint}:{cache_key}"
_BI_RATE_KEY = "bi-rate:{user_id}:{endpoint}"


def _get_redis_client():
    redis_client = current_app.extensions.get('redis_client')
    if not redis_client:  # pragma: no cover - 初始化錯誤時提醒
        raise RuntimeError('Redis 尚未初始化，請確認 create_app 是否執行 _init_redis_client')
    return redis_client


def get_dashboard_cache(user_id: int) -> Optional[Any]:
    client = _get_redis_client()
    raw = client.get(_CACHE_KEY.format(user_id=user_id))
    if not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def set_dashboard_cache(user_id: int, payload: Any) -> None:
    client = _get_redis_client()
    client.setex(
        _CACHE_KEY.format(user_id=user_id),
        CACHE_TTL_SECONDS,
        json.dumps(payload),
    )


def clear_dashboard_cache(user_id: int) -> None:
    client = _get_redis_client()
    client.delete(_CACHE_KEY.format(user_id=user_id))


def get_user_lock(user_id: int):
    client = _get_redis_client()
    return client.lock(
        _LOCK_KEY.format(user_id=user_id),
        timeout=CACHE_TTL_SECONDS,
        blocking_timeout=5,
    )


def get_bi_cache(user_id: int, endpoint: str, cache_key: str) -> Optional[Any]:
    client = _get_redis_client()
    raw = client.get(_BI_CACHE_KEY.format(user_id=user_id, endpoint=endpoint, cache_key=cache_key))
    if not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def set_bi_cache(user_id: int, endpoint: str, cache_key: str, payload: Any, ttl: int = BI_CACHE_TTL_SECONDS) -> None:
    client = _get_redis_client()
    client.setex(
        _BI_CACHE_KEY.format(user_id=user_id, endpoint=endpoint, cache_key=cache_key),
        ttl,
        json.dumps(payload),
    )


def clear_bi_cache(user_id: int, endpoint: str) -> None:
    client = _get_redis_client()
    pattern = _BI_CACHE_KEY.format(user_id=user_id, endpoint=endpoint, cache_key='*')
    keys = client.keys(pattern)
    if not keys:
        return
    for key in keys:
        client.delete(key)


def check_bi_rate_limit(user_id: int, endpoint: str, limit: int | None = None) -> bool:
    client = _get_redis_client()
    key = _BI_RATE_KEY.format(user_id=user_id, endpoint=endpoint)
    current_limit = BI_RATE_LIMIT_PER_MINUTE if limit is None else limit
    current = client.incr(key)
    if current == 1:
        client.expire(key, _BI_RATE_WINDOW_SECONDS)
    return current <= current_limit
