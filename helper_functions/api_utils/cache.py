"""Simple caching layer for team IDs, logos, and API responses.

Reduces redundant API calls and improves performance by caching frequently accessed data.
"""
from __future__ import annotations

import time
from functools import wraps
from typing import TYPE_CHECKING, TypeVar

from helper_functions.logging.logger_config import logger, track_cache_hit, track_cache_miss

if TYPE_CHECKING:
    from collections.abc import Callable

# Global cache storage
_cache: dict[str, object] = {}
_cache_timestamps: dict[str, float] = {}
_cache_ttl: dict[str, int] = {}

# Default TTL values (in seconds)
TEAM_ID_TTL = 86400  # 24 hours - team IDs rarely change
LOGO_TTL = 604800  # 7 days - logos rarely change
API_RESPONSE_TTL = 60  # 1 minute - live data changes frequently

T = TypeVar("T")


def cache_result(ttl: int = API_RESPONSE_TTL, key_prefix: str = "") -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Cache function results with TTL.

    :param ttl: Time-to-live in seconds
    :param key_prefix: Prefix for cache key (e.g., 'team_id', 'logo')
    :return: Decorated function
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: object, **kwargs: object) -> T:
            # Create cache key from function name and arguments
            key_parts = [key_prefix or func.__name__]
            key_parts.extend(str(arg) for arg in args)
            key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
            cache_key = ":".join(key_parts)

            # Check if cached value exists and is not expired
            if cache_key in _cache:
                age = time.time() - _cache_timestamps.get(cache_key, 0)
                if age < _cache_ttl.get(cache_key, ttl):
                    track_cache_hit()
                    logger.debug(f"Cache hit: {cache_key} (age: {age:.0f}s)")
                    return _cache[cache_key]  # type: ignore[return-value]
                logger.debug(
                    "Cache expired: %s (age: %.0fs > %ss)",
                    cache_key,
                    age,
                    _cache_ttl.get(cache_key, ttl),
                )

            # Call function and cache result
            track_cache_miss()
            result = func(*args, **kwargs)
            _cache[cache_key] = result
            _cache_timestamps[cache_key] = time.time()
            _cache_ttl[cache_key] = ttl
            logger.debug(f"Cache set: {cache_key}")
            return result

        return wrapper
    return decorator


def get_cached(key: str, max_age: int | None = None) -> object | None:
    """Get cached value by key.

    :param key: Cache key
    :param max_age: Maximum age in seconds (overrides TTL for staleness check)
    :return: Cached value or None if not found or too old
    """
    if key not in _cache:
        return None

    age = time.time() - _cache_timestamps.get(key, 0)

    # Check max_age first (stricter staleness limit)
    if max_age is not None and age >= max_age:
        logger.debug("Cache too stale for key %s (age %.0fs >= %ss max)", key, age, max_age)
        return None

    # Check normal TTL expiration
    ttl = _cache_ttl.get(key, API_RESPONSE_TTL)
    if age >= ttl:
        logger.debug("Cache expired for key %s (age %.0fs >= %ss)", key, age, ttl)
        _cache.pop(key, None)
        _cache_timestamps.pop(key, None)
        _cache_ttl.pop(key, None)
        return None

    return _cache[key]


def set_cached(key: str, value: object, ttl: int = API_RESPONSE_TTL) -> None:
    """Set cached value with TTL.

    :param key: Cache key
    :param value: Value to cache
    :param ttl: Time-to-live in seconds
    """
    _cache[key] = value
    _cache_timestamps[key] = time.time()
    _cache_ttl[key] = ttl
    logger.debug("Cache manually set: %s", key)


def clear_cache(key: str | None = None) -> None:
    """Clear cache entries.

    :param key: Specific key to clear, or None to clear all
    """
    if key is None:
        _cache.clear()
        _cache_timestamps.clear()
        _cache_ttl.clear()
        logger.info("Cleared all cache entries")
    elif key in _cache:
        del _cache[key]
        del _cache_timestamps[key]
        _cache_ttl.pop(key, None)
        logger.info("Cleared cache entry: %s", key)


def get_cache_stats() -> dict[str, object]:
    """Get cache statistics.

    :return: Dict with cache size, oldest entry, etc.
    """
    if not _cache:
        return {"size": 0, "entries": 0}

    oldest_age = max(time.time() - ts for ts in _cache_timestamps.values()) if _cache_timestamps else 0
    return {
        "size": len(_cache),
        "entries": list(_cache.keys()),
        "oldest_entry_age": oldest_age,
    }
