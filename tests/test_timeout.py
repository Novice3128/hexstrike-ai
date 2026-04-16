"""
Tests for timeout propagation through execute_command → EnhancedCommandExecutor.
Run: cd external/hexstrike-ai/tests && python -m pytest test_timeout.py -v
"""
import pytest
import json
from unittest.mock import patch, MagicMock


def test_execute_command_explicit_timeout():
    """Verify explicit timeout parameter reaches EnhancedCommandExecutor"""
    from hexstrike_server import execute_command

    with patch("hexstrike_server.EnhancedCommandExecutor") as MockExecutor:
        mock_instance = MagicMock()
        mock_instance.execute.return_value = {"success": True, "stdout": "ok", "returncode": 0}
        MockExecutor.return_value = mock_instance

        execute_command("echo test", no_cache=True, timeout=10)

        MockExecutor.assert_called_once_with("echo test", timeout=10)


def test_execute_command_default_timeout():
    """Verify default timeout is COMMAND_TIMEOUT (300) when none specified"""
    from hexstrike_server import execute_command, COMMAND_TIMEOUT, app

    with patch("hexstrike_server.EnhancedCommandExecutor") as MockExecutor:
        mock_instance = MagicMock()
        mock_instance.execute.return_value = {"success": True, "stdout": "ok", "returncode": 0}
        MockExecutor.return_value = mock_instance

        with app.test_request_context(json={}):
            execute_command("echo test", no_cache=True)

        MockExecutor.assert_called_once_with("echo test", timeout=COMMAND_TIMEOUT)


def test_auto_detect_timeout_from_request():
    """Verify timeout auto-detected from Flask request JSON body"""
    from hexstrike_server import execute_command, app

    with patch("hexstrike_server.EnhancedCommandExecutor") as MockExecutor:
        mock_instance = MagicMock()
        mock_instance.execute.return_value = {"success": True, "stdout": "ok", "returncode": 0}
        MockExecutor.return_value = mock_instance

        request_data = {"timeout": 45, "domain": "test.com"}
        with app.test_request_context(
            json=request_data,
            method="POST"
        ):
            execute_command("echo test", no_cache=True)

        MockExecutor.assert_called_once_with("echo test", timeout=45)


def test_auto_detect_ignores_missing_timeout():
    """Verify auto-detection falls back to COMMAND_TIMEOUT when timeout not in JSON"""
    from hexstrike_server import execute_command, COMMAND_TIMEOUT, app

    with patch("hexstrike_server.EnhancedCommandExecutor") as MockExecutor:
        mock_instance = MagicMock()
        mock_instance.execute.return_value = {"success": True, "stdout": "ok", "returncode": 0}
        MockExecutor.return_value = mock_instance

        with app.test_request_context(json={"domain": "test.com"}):
            execute_command("echo test", no_cache=True)

        MockExecutor.assert_called_once_with("echo test", timeout=COMMAND_TIMEOUT)


def test_no_request_context_uses_default():
    """Verify graceful fallback when not in Flask request context"""
    from hexstrike_server import execute_command, COMMAND_TIMEOUT

    with patch("hexstrike_server.EnhancedCommandExecutor") as MockExecutor:
        mock_instance = MagicMock()
        mock_instance.execute.return_value = {"success": True, "stdout": "ok", "returncode": 0}
        MockExecutor.return_value = mock_instance

        # No test_request_context — execute_command handles RuntimeError internally
        execute_command("echo test", no_cache=True)

        MockExecutor.assert_called_once_with("echo test", timeout=COMMAND_TIMEOUT)


def test_explicit_timeout_overrides_auto_detect():
    """Verify explicit timeout parameter takes precedence over auto-detected value"""
    from hexstrike_server import execute_command, app

    with patch("hexstrike_server.EnhancedCommandExecutor") as MockExecutor:
        mock_instance = MagicMock()
        mock_instance.execute.return_value = {"success": True, "stdout": "ok", "returncode": 0}
        MockExecutor.return_value = mock_instance

        request_data = {"timeout": 999}
        with app.test_request_context(
            json=request_data,
            method="POST"
        ):
            execute_command("echo test", no_cache=True, timeout=15)

        MockExecutor.assert_called_once_with("echo test", timeout=15)
