import redis
import json
import os
from functools import wraps
from fastapi import HTTPException

# Redis connection
redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    db=0,
    decode_responses=True,
)


def cache_response(expire_time: int = 300):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Create a cache key based on function name and arguments
            key_parts = (
                [func.__name__]
                + [str(arg) for arg in args]
                + [f"{k}={v}" for k, v in kwargs.items()]
            )
            cache_key = ":".join(key_parts)

            # Try to get cached result
            cached_result = redis_client.get(cache_key)
            if cached_result:
                return json.loads(cached_result)

            # Execute function if not cached
            result = await func(*args, **kwargs)

            # Cache the result
            redis_client.setex(cache_key, expire_time, json.dumps(result))

            return result

        return wrapper

    return decorator


def invalidate_cache(pattern: str):
    keys = redis_client.keys(pattern)
    if keys:
        redis_client.delete(*keys)
