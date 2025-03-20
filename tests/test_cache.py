"""Tests for the Cache module."""

import pytest
from time import sleep
from app.cache import Cache


def test_cache_hit():
    """Test cache returns correct value on cache hit."""
    cache = Cache(maxsize=128, ttl=86400)
    cache.set("test_key", "test_value")
    assert cache.get("test_key") == "test_value"


def test_cache_miss():
    """Test cache returns None on cache miss."""
    cache = Cache(maxsize=128, ttl=86400)
    assert cache.get("nonexistent_key") is None


def test_cache_ttl():
    """Test cache TTL functionality."""
    cache = Cache(maxsize=128, ttl=1)  # 1 second TTL for testing
    cache.set("test_key", "test_value")
    assert cache.get("test_key") == "test_value"
    sleep(2)  # Wait for TTL to expire
    assert cache.get("test_key") is None


def test_cache_invalidate():
    """Test manual cache invalidation."""
    cache = Cache(maxsize=128, ttl=86400)
    cache.set("test_key", "test_value")
    assert cache.get("test_key") == "test_value"
    cache.invalidate("test_key")
    assert cache.get("test_key") is None


def test_cache_maxsize():
    """Test cache respects maxsize limit."""
    cache = Cache(maxsize=2, ttl=86400)
    cache.set("key1", "value1")
    cache.set("key2", "value2")
    cache.set("key3", "value3")  # Should evict oldest item
    assert cache.get("key1") is None  # Should have been evicted
    assert cache.get("key2") == "value2"
    assert cache.get("key3") == "value3"
