from __future__ import annotations

import uuid
from typing import Any

from app.core.errors import AppError, ErrorCode
from app.integrations.servicenow.base import ServiceNowBaseClient
from app.repositories.servicenow_mock_records import create_record, get_record, update_record


class MockServiceNowClient(ServiceNowBaseClient):
    """In-process mock ServiceNow adapter used in Phase 2."""

    _IMPACT_VALUES = {"organization": 1, "group": 2, "individual": 3}
    _URGENCY_VALUES = {"high": 1, "medium": 2, "low": 3}
    _STATUS_VALUES = {"open": 1, "in_progress": 2, "resolved": 6, "closed": 7}

    def _make_number(self, prefix: str, seed: int) -> str:
        return f"{prefix}{seed:06d}"

    def create_incident(
        self, db: Any, payload: dict[str, Any], *, session: Any = None
    ) -> dict[str, Any]:
        sys_id = uuid.uuid4().hex[:32]
        number = payload.get("number") or self._make_number("INC", int(uuid.uuid4().hex[:8], 16) % 1000000)
        record = {
            "_id": sys_id,
            "mode": "mock",
            "record_type": "incident",
            "number": number,
            "sys_id": sys_id,
            "fields": {
                "short_description": payload.get("short_description"),
                "description": payload.get("description"),
                "category": payload.get("category"),
                "subcategory": payload.get("subcategory"),
                "impact": self._IMPACT_VALUES[payload["impact"]],
                "urgency": self._URGENCY_VALUES[payload["urgency"]],
                "priority": int(payload["priority"][1:]),
                "assignment_group": payload.get("assignment_group"),
                "caller_id": payload.get("employee_id"),
                "state": self._STATUS_VALUES["open"],
            },
            "work_notes": [],
            "created_at": payload.get("created_at"),
            "updated_at": payload.get("created_at"),
        }
        create_record(db, record, session=session)
        return {
            "mode": "mock",
            "record_type": "incident",
            "number": number,
            "sys_id": sys_id,
        }

    def update_incident(self, db: Any, sys_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        record = get_record(db, sys_id)
        if record is None:
            raise AppError(
                code=ErrorCode.SERVICENOW_UNAVAILABLE,
                message="The mock ServiceNow incident could not be found.",
                http_status=502,
            )
        updated_at = payload.get("updated_at")
        fields = dict(record.get("fields", {}))
        if "status" in payload:
            fields["state"] = self._STATUS_VALUES[payload["status"]]
        if "work_note" in payload and payload["work_note"]:
            record.setdefault("work_notes", []).append(
                {"timestamp": updated_at, "text": payload["work_note"]}
            )
        patch = {"fields": fields, "work_notes": record.get("work_notes", [])}
        if updated_at is not None:
            patch["updated_at"] = updated_at
        updated = update_record(db, sys_id, patch)
        if updated is None:
            raise AppError(
                code=ErrorCode.SERVICENOW_UNAVAILABLE,
                message="The mock ServiceNow incident could not be updated.",
                http_status=502,
            )
        return {
            "mode": "mock",
            "record_type": "incident",
            "number": updated["number"],
            "sys_id": sys_id,
            "status": payload.get("status"),
        }

    def create_service_request(self, db: Any, payload: dict[str, Any]) -> dict[str, Any]:
        sys_id = uuid.uuid4().hex[:32]
        number = self._make_number("REQ", int(uuid.uuid4().hex[:8], 16) % 1000000)
        record = {
            "_id": sys_id,
            "mode": "mock",
            "record_type": "service_request",
            "number": number,
            "sys_id": sys_id,
            "software": payload.get("software_name"),
            "status": "submitted",
            "employee_id": payload.get("employee_id"),
        }
        create_record(db, record)
        return {
            "mode": "mock",
            "record_type": "service_request",
            "number": number,
            "sys_id": sys_id,
        }

    def update_service_request(self, db: Any, sys_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        record = get_record(db, sys_id)
        if record is None:
            raise AppError(
                code=ErrorCode.SERVICENOW_UNAVAILABLE,
                message="The mock ServiceNow service request could not be found.",
                http_status=502,
            )
        patch = {}
        if "status" in payload:
            patch["status"] = payload["status"]
        if "detail" in payload:
            patch["detail"] = payload["detail"]
        if "updated_at" in payload:
            patch["updated_at"] = payload["updated_at"]
        updated = update_record(db, sys_id, patch)
        return {
            "mode": "mock",
            "record_type": "service_request",
            "number": record["number"],
            "sys_id": sys_id,
            "status": payload.get("status"),
        }

