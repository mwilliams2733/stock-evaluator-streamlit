"""File-based caching layer with TTL support."""
import json
import os
import pickle
import time
from pathlib import Path

CACHE_DIR = Path(__file__).resolve().parent.parent / "cache"
CACHE_DIR.mkdir(exist_ok=True)


def _cache_path(key: str, fmt: str = "json") -> Path:
    safe_key = key.replace("/", "_").replace(":", "_").replace("?", "_")
    return CACHE_DIR / f"{safe_key}.{fmt}"


def get_cached(key: str, ttl: int = 86400, fmt: str = "json"):
    """Retrieve cached data if it exists and hasn't expired.

    Args:
        key: Cache key identifier.
        ttl: Time-to-live in seconds.
        fmt: 'json' or 'pickle'.

    Returns:
        Cached data or None if expired/missing.
    """
    path = _cache_path(key, fmt)
    if not path.exists():
        return None
    if time.time() - path.stat().st_mtime > ttl:
        return None
    try:
        if fmt == "json":
            with open(path, "r") as f:
                return json.load(f)
        else:
            with open(path, "rb") as f:
                return pickle.load(f)
    except Exception:
        return None


def set_cached(key: str, data, fmt: str = "json"):
    """Store data in the cache.

    Args:
        key: Cache key identifier.
        data: Data to cache.
        fmt: 'json' or 'pickle'.
    """
    path = _cache_path(key, fmt)
    try:
        if fmt == "json":
            with open(path, "w") as f:
                json.dump(data, f)
        else:
            with open(path, "wb") as f:
                pickle.dump(data, f)
    except Exception:
        pass


def clear_cache():
    """Remove all cached files."""
    for f in CACHE_DIR.iterdir():
        if f.is_file() and f.suffix in (".json", ".pickle"):
            f.unlink()


def cache_stats() -> dict:
    """Return cache statistics."""
    files = list(CACHE_DIR.iterdir())
    cache_files = [f for f in files if f.is_file() and f.suffix in (".json", ".pickle")]
    total_size = sum(f.stat().st_size for f in cache_files)
    return {
        "file_count": len(cache_files),
        "total_size_mb": round(total_size / (1024 * 1024), 2),
    }
