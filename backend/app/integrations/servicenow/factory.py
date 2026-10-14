from __future__ import annotations

from app.core.config import get_settings
from app.integrations.servicenow.mock_client import MockServiceNowClient


def get_servicenow_client():
    """Return the configured ServiceNow adapter for the current app mode."""
    settings = get_settings()
    if settings.servicenow_mode == "mock":
        return MockServiceNowClient()
    raise RuntimeError("Unsupported ServiceNow mode for Phase 2: %s" % settings.servicenow_mode)
