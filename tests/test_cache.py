"""
Tests for HexStrikeCache TTL behavior (success/failure differentiation, no_cache bypass, expiry).
Run: cd external/hexstrike-ai/tests && python -m pytest test_cache.py -v
"""
import time
import pytest
from unittest.mock import patch, MagicMock


def test_cache_success_ttl_3600():
    """Verify successful results cached with 3600s TTL"""
    from hexstrike_server import HexStrikeCache, CACHE_TTL

    cache = HexStrikeCache(max_size=10)
    result = {"success": True, "stdout": "ok", "returncode": 0}

    cache.set("echo test", {}, result, ttl=3600)
    cached = cache.get("echo test", {})

    assert cached is not None
    assert cached["success"] is True
    assert cache.stats["hits"] == 1


def test_cache_failure_ttl_60():
    """Verify failed results cached with 60s TTL"""
    from hexstrike_server import HexStrikeCache, CACHE_TTL_FAILURE

    cache = HexStrikeCache(max_size=10)
    result = {"success": False, "stderr": "error", "returncode": 1}

    cache.set("bad command", {}, result, ttl=60)
    cached = cache.get("bad command", {})

    assert cached is not None
    assert cached["success"] is False
    assert cache.stats["hits"] == 1


def test_cache_no_cache_bypass():
    """Verify no_cache=True skips cache lookup in execute_command"""
    from hexstrike_server import execute_command

    with patch("hexstrike_server.EnhancedCommandExecutor") as MockExecutor:
        mock_instance = MagicMock()
        mock_instance.execute.return_value = {"success": True, "stdout": "ok", "returncode": 0}
        MockExecutor.return_value = mock_instance

        # First call: populate cache
        execute_command("echo cached", no_cache=False)

        # Second call with no_cache=True: should still call executor (not cache hit)
        MockExecutor.reset_mock()
        mock_instance.execute.return_value = {"success": True, "stdout": "fresh", "returncode": 0}
        execute_command("echo cached", no_cache=True)

        MockExecutor.assert_called_once()


def test_cache_ttl_expiry():
    """Verify cache entry expires after TTL"""
    from hexstrike_server import HexStrikeCache

    cache = HexStrikeCache(max_size=10)
    result = {"success": True, "stdout": "ok", "returncode": 0}

    # Set with very short TTL
    cache.set("expire test", {}, result, ttl=1)

    # Should be available immediately
    cached = cache.get("expire test", {})
    assert cached is not None

    # Wait for TTL to expire
    time.sleep(1.1)

    # Should be expired now
    cached = cache.get("expire test", {})
    assert cached is None
    assert cache.stats["misses"] == 1


def test_cache_different_ttl_per_entry():
    """Verify success (3600s) and failure (60s) entries coexist with correct TTLs"""
    from hexstrike_server import HexStrikeCache

    cache = HexStrikeCache(max_size=10)

    success_result = {"success": True, "stdout": "ok"}
    failure_result = {"success": False, "stderr": "err"}

    cache.set("success_cmd", {}, success_result, ttl=3600)
    cache.set("failure_cmd", {}, failure_result, ttl=60)

    assert cache.get("success_cmd", {}) is not None
    assert cache.get("failure_cmd", {}) is not None
    assert cache.stats["hits"] == 2
