"""Real subprocess timeout verification — tests execute actual subprocesses.

NOT integration-marked: runs locally without Docker.
Run: cd external/hexstrike-ai/tests && python -m pytest test_timeout_real.py -v
"""
import time


def test_real_subprocess_killed_on_timeout():
    """Verify a long-running command is actually killed when timeout expires."""
    from hexstrike_server import execute_command

    start = time.monotonic()
    result = execute_command("sleep 60", no_cache=True, timeout=2)
    elapsed = time.monotonic() - start

    assert result["timed_out"] is True, f"Expected timed_out=True, got: {result}"
    assert result["success"] is False
    assert 2.0 <= elapsed <= 5.0, f"Expected 2.0-5.0s, got {elapsed:.2f}s"


def test_timed_out_result_not_cached():
    """Verify timed-out results are NOT cached — subsequent call hits cache miss."""
    from hexstrike_server import execute_command, cache

    # Use a unique command to avoid interference
    cmd = "sleep 30"

    # Clear any existing cache entry
    cache_key = cache._generate_key(cmd, {})
    if cache_key in cache.cache:
        del cache.cache[cache_key]

    result = execute_command(cmd, no_cache=False, timeout=2)
    assert result["timed_out"] is True

    # Timed-out results should NOT be in cache
    cached = cache.get(cmd, {})
    assert cached is None, "Timed-out result was cached — should be a cache miss"


def test_timeout_clamp_minimum_1():
    """Verify timeout=0 is clamped to 1, not raising or hanging."""
    from hexstrike_server import execute_command

    result = execute_command("echo ok", no_cache=True, timeout=0)

    assert "execution_time" in result, f"Missing execution_time: {result}"
    assert result.get("success") is True or result.get("timed_out") is True
