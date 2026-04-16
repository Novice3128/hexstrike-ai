"""Integration tests — require running arxon-hexstrike-ai container.
Run: cd external/hexstrike-ai/tests && python -m pytest test_integration.py -v -m integration
Skip when container not available.
"""
import pytest
import subprocess

pytestmark = pytest.mark.integration


def _docker_exec(cmd: str):
    result = subprocess.run(
        ["docker", "exec", "arxon-hexstrike-ai", "bash", "-c", cmd],
        capture_output=True, text=True, timeout=30
    )
    return result.stdout.strip(), result.stderr.strip(), result.returncode


@pytest.fixture(autouse=True)
def skip_if_no_container():
    """Skip all tests if container is not running."""
    try:
        stdout, _, rc = _docker_exec("echo ok")
        if rc != 0 or stdout != "ok":
            pytest.skip("arxon-hexstrike-ai container not running")
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pytest.skip("docker not available or container not running")


def test_execute_command_has_timeout_param():
    stdout, stderr, rc = _docker_exec(
        "python3 -c \"from hexstrike_server import execute_command; import inspect; "
        "sig=inspect.signature(execute_command); "
        "assert 'timeout' in sig.parameters, f'Missing: {sig}'; print('OK')\""
    )
    assert rc == 0 and "OK" in stdout, f"Failed: rc={rc}, stdout={stdout}, stderr={stderr}"


def test_cache_ttl_failure_is_60():
    stdout, stderr, rc = _docker_exec(
        "python3 -c \"from hexstrike_server import CACHE_TTL_FAILURE; "
        "assert CACHE_TTL_FAILURE==60; print('OK')\""
    )
    assert rc == 0 and "OK" in stdout, f"Failed: rc={rc}, stdout={stdout}, stderr={stderr}"


def test_cache_ttl_success_is_3600():
    stdout, stderr, rc = _docker_exec(
        "python3 -c \"from hexstrike_server import CACHE_TTL; "
        "assert CACHE_TTL==3600; print('OK')\""
    )
    assert rc == 0 and "OK" in stdout, f"Failed: rc={rc}, stdout={stdout}, stderr={stderr}"
