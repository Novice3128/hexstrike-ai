"""
conftest.py for hexstrike-ai tests.
Adds parent directory to sys.path and mocks unavailable container-only dependencies
(selenium, mitmproxy) so hexstrike_server can be imported on the host.
Run tests from this directory: cd external/hexstrike-ai/tests && python -m pytest -v
"""
import sys
import os
from unittest.mock import MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock container-only dependencies not available on host
_MOCK_MODULES = {
    "selenium": MagicMock(),
    "selenium.webdriver": MagicMock(),
    "selenium.webdriver.chrome": MagicMock(),
    "selenium.webdriver.chrome.options": MagicMock(),
    "selenium.webdriver.common": MagicMock(),
    "selenium.webdriver.common.by": MagicMock(),
    "selenium.webdriver.support": MagicMock(),
    "selenium.webdriver.support.ui": MagicMock(),
    "selenium.webdriver.support.expected_conditions": MagicMock(),
    "selenium.common": MagicMock(),
    "selenium.common.exceptions": MagicMock(),
    "mitmproxy": MagicMock(),
    "mitmproxy.http": MagicMock(),
    "mitmproxy.tools": MagicMock(),
    "mitmproxy.tools.dump": MagicMock(),
    "mitmproxy.options": MagicMock(),
}

for mod_name, mod_mock in _MOCK_MODULES.items():
    sys.modules.setdefault(mod_name, mod_mock)
