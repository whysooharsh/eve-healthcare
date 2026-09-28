import json
import os

try:
    import redis
except ImportError:
    redis = None

_client = None


def get_client():
    global _client
    if _client is not None:
        return _client
    url = os.getenv("REDIS_URL", "")
    if not url or redis is None:
        return None
    try:
        _client = redis.Redis.from_url(url, socket_connect_timeout=2)
        _client.ping()
    except Exception:
        _client = None
    return _client


def get_json(key: str):
    client = get_client()
    if client is None:
        return None
    try:
        raw = client.get(key)
    except Exception:
        return None
    return json.loads(raw) if raw else None


def set_json(key: str, value, ttl: int = 60) -> None:
    client = get_client()
    if client is None:
        return
    try:
        client.setex(key, ttl, json.dumps(value, default=str))
    except Exception:
        return


def invalidate(*prefixes: str) -> None:
    client = get_client()
    if client is None:
        return
    try:
        for prefix in prefixes:
            for key in client.scan_iter(f"{prefix}*"):
                client.delete(key)
    except Exception:
        return
