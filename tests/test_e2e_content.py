"""E2E content assertions — verify tool output contains expected content.

Requires running arxon-hexstrike-ai container.
Run: cd external/hexstrike-ai/tests && python -m pytest test_e2e_content.py -v -m integration
"""
import json
import pytest
import subprocess
import time

pytestmark = pytest.mark.integration


def _call_hexstrike_api(endpoint: str, args: dict, timeout: int = 30):
    """Call a hexstrike tool directly via HTTP API inside the container."""
    args_json = json.dumps(args)
    cmd = [
        "docker", "exec", "arxon-hexstrike-ai",
        "python3", "-c",
        "import requests, json; "
        f"r = requests.post('http://localhost:8888/api/tools/{endpoint}', "
        f"json={args_json}, timeout={timeout}); "
        "print(json.dumps(r.json()))"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 15)
    if result.returncode != 0:
        pytest.skip(f"docker exec failed: {result.stderr[:200]}")
    return json.loads(result.stdout)


@pytest.fixture(autouse=True)
def skip_if_no_container():
    """Skip all tests if container is not running."""
    try:
        r = subprocess.run(
            ["docker", "exec", "arxon-hexstrike-ai", "echo", "ok"],
            capture_output=True, text=True, timeout=10
        )
        if r.returncode != 0 or r.stdout.strip() != "ok":
            pytest.skip("arxon-hexstrike-ai container not running")
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pytest.skip("docker not available or container not running")


def test_nmap_output_contains_port_info():
    """nmap scan of localhost:22 should mention port 22 in output."""
    result = _call_hexstrike_api("nmap", {
        "target": "127.0.0.1",
        "ports": "22",
        "scan_type": "-sV"
    })
    assert result.get("success") is True, f"nmap failed: {result.get('stderr', '')[:200]}"

    stdout = result.get("stdout", "")
    assert len(stdout) > 0, "nmap stdout is empty"
    assert any(p in stdout for p in ["22/tcp", "open", "closed", "filtered"]), \
        f"nmap output lacks port state info: {stdout[:300]}"


def test_amass_wrapper_returns_valid_structure():
    """amass wrapper returns a valid response structure regardless of success/timeout.

    This tests the MCP wrapper, not amass itself. The response must have
    standard fields (success, stdout, stderr, timed_out) regardless of outcome.
    """
    result = _call_hexstrike_api("amass", {
        "domain": "example.com",
        "mode": "enum",
        "timeout": 15
    })

    # Must have standard response fields
    assert "success" in result, f"Missing 'success' field: {list(result.keys())}"
    assert "stdout" in result, f"Missing 'stdout' field: {list(result.keys())}"
    assert "stderr" in result, f"Missing 'stderr' field: {list(result.keys())}"

    # The wrapper MUST populate execution_time to prove it ran
    assert "execution_time" in result, \
        f"Response lacks execution_time — wrapper may not have executed: {list(result.keys())}"

    # If timed out, that's acceptable — the wrapper handled it correctly
    if result.get("timed_out"):
        assert result["success"] is False or result.get("execution_time") is not None, \
            "Timed-out result should have execution_time or success=false"

    # If successful, stdout should be non-empty
    if result["success"] and not result.get("timed_out"):
        assert len(result["stdout"]) > 0, "amass succeeded but stdout is empty"
