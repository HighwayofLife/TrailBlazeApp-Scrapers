"""Cache module for storing HTML content with TTL functionality."""

from typing import Any, Optional
from cachetools import TTLCache
import cachetools
import time


class Cache:
    """
    Cache implementation using TTLCache for storing HTML content.

    Provides caching functionality with time-to-live (TTL) feature to prevent
    unnecessary network requests by storing HTML content temporarily.
    """

    def __init__(self, maxsize: int = 128, ttl: int = 86400) -> None:
        """
        Initialize the Cache.

        Args:
            maxsize (int): Maximum number of items in cache (default: 128)
            ttl (int): Time-to-live in seconds (default: 86400 (24 hours))
        """
        self.cache = cachetools.TTLCache(maxsize=maxsize, ttl=ttl)

    def get(self, key: str) -> Optional[str]:
        """
        Retrieve cached value for given key if it exists and is not expired.

        Args:
            key (str): Cache key to look up

        Returns:
            Optional[str]: Cached value if found and valid, None otherwise
        """
        try:
            return self.cache[key]
        except KeyError:
            return None

    def set(self, key: str, value: str) -> None:
        """
        Store value in cache with given key.

        Args:
            key (str): Cache key to store value under
            value (str): Value to cache
        """
        self.cache[key] = value

    def invalidate(self, key: str) -> None:
        """
        Remove given key from cache.

        Args:
            key (str): Cache key to remove
        """
        try:
            del self.cache[key]
        except KeyError:
            pass
