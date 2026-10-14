from __future__ import annotations

from typing import Any


class ServiceNowBaseClient:
    """Common contract for ServiceNow integrations."""

    def create_incident(
        self, db: Any, payload: dict[str, Any], *, session: Any = None
    ) -> dict[str, Any]:
        raise NotImplementedError

    def update_incident(self, db: Any, sys_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError

    def create_service_request(self, db: Any, payload: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError

    def update_service_request(self, db: Any, sys_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError

