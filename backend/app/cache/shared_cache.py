# app/cache/shared_cache.py
import redis
import json
from typing import Any, Optional
from app.core.config import settings
from datetime import datetime, date

try:
    shared_redis_client = redis.Redis.from_url(settings.SHARED_CACHE_REDIS_URL, decode_responses=True)
    shared_redis_client.ping()
    print("SHARED_CACHE: Successfully connected to Redis for shared cache.")
except redis.exceptions.ConnectionError as e:
    print(f"SHARED_CACHE_ERROR: Could not connect to Redis for shared cache: {e}")
    shared_redis_client = None

CACHE_DURATION_SECONDS = 15 * 60


def get_shared_cache(key: str) -> Optional[Any]:
    if not shared_redis_client:
        return None
    try:
        cached_value_json = shared_redis_client.get(key)
        if cached_value_json:
            return json.loads(cached_value_json)
        return None
    except Exception as e:
        print(f"SHARED_CACHE_ERROR: Error getting from Redis key {key}: {e}")
        return None


def _datetime_converter(o):
    if isinstance(o, (datetime, date)):
        return o.isoformat()
    raise TypeError(f"Object of type {o.__class__.__name__} is not JSON serializable")


def set_shared_cache(key: str, value: Any, ex: int = CACHE_DURATION_SECONDS):
    if not shared_redis_client or value is None:
        return
    try:
        json_value = json.dumps(value, default=_datetime_converter)
        shared_redis_client.set(key, json_value, ex=ex)
        print(f"SHARED_CACHE_SET: Set key {key}")
    except Exception as e:
        print(f"SHARED_CACHE_ERROR: Error setting to Redis key {key}: {e}")
