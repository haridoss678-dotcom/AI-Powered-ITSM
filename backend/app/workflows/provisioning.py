"""
Sorim.AI — Software Provisioning Workflow  (workflows/provisioning.py)

Manages the software request lifecycle per ARCHITECTURE.md §8:
Intent -> Catalogue lookup -> ServiceNow mock request -> Mock provisioning -> Validation -> Status update -> Audit.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.core.errors import AppError, ErrorCode
from app.integrations.provisioning.mock_provisioner import get_mock_provisioner
from app.integrations.servicenow.factory import get_servicenow_client
from app.repositories.sequences import get_next_sequence
from app.repositories.software_requests import get_request, insert_request, update_request
from app.repositories.users import get_user
from app.schemas.common import SoftwareRequestStatus
from app.schemas.software import (
    EmployeeSnapshot,
    ProvisioningInfo,
    SoftwareRequest,
    SoftwareServiceNowRef,
    SoftwareSnapshot,
)
from app.services.audit_service import log_audit_event
from app.services.software_catalogue import match_software


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def handle_software_request(
    db: Any,
    *,
    employee_id: str,
    software_name: str,
    request_id: str | None = None,
) -> SoftwareRequest:
    user = get_user(db, employee_id)
    if user is None:
        raise AppError(
            code=ErrorCode.EMPLOYEE_NOT_FOUND,
            message=f"Employee '{employee_id}' was not found.",
            http_status=404,
        )

    matched = match_software(software_name)
    if matched is None:
        log_audit_event(
            db,
            actor="employee",
            event_type="software.request_created",
            outcome="failure",
            request_id=request_id,
            mode="mock",
            details={"software_name": software_name, "error": "Software not in catalogue"},
        )
        raise AppError(
            code=ErrorCode.SOFTWARE_NOT_IN_CATALOGUE,
            message=f"Requested software '{software_name}' is not in the approved corporate catalogue.",
            http_status=422,
        )

    seq = get_next_sequence(db, "software_request")
    software_request_id = f"SWR-{seq:06d}"
    created_at = _now()

    # 1. Create ServiceNow mock service request
    sn_client = get_servicenow_client()
    try:
        sn_ref_raw = sn_client.create_service_request(
            db,
            {
                "employee_id": employee_id,
                "software_name": matched.name,
                "created_at": created_at,
            },
        )
    except Exception as exc:
        log_audit_event(
            db,
            actor="system",
            event_type="servicenow.failed",
            outcome="failure",
            request_id=request_id,
            mode="mock",
            details={"operation": "create_service_request", "error": str(exc)},
        )
        raise AppError(
            code=ErrorCode.SERVICENOW_UNAVAILABLE,
            message="Failed to create ServiceNow service request.",
            http_status=502,
        ) from exc

    sn_ref = SoftwareServiceNowRef(
        mode="mock",
        record_type="service_request",
        number=sn_ref_raw["number"],
        sys_id=sn_ref_raw["sys_id"],
    )

    # 2. Start mock provisioning
    provisioner = get_mock_provisioner()
    job_id = provisioner.start_job(matched.name, employee_id)

    prov_info = ProvisioningInfo(
        mode="mock",
        job_id=job_id,
        detail=f"Automated mock package deployment scheduled for {matched.name}.",
        started_at=created_at,
        completed_at=None,
    )

    doc: dict[str, Any] = {
        "_id": software_request_id,
        "software_request_id": software_request_id,
        "employee": {"employee_id": employee_id, "name": user.get("name", "")},
        "software": {
            "catalogue_id": matched.catalogue_id,
            "name": matched.name,
            "version": matched.version,
        },
        "status": SoftwareRequestStatus.provisioning.value,
        "servicenow_ref": sn_ref.model_dump(),
        "provisioning": prov_info.model_dump(),
        "request_id": request_id,
        "created_at": created_at,
        "updated_at": created_at,
    }
    insert_request(db, doc)

    log_audit_event(
        db,
        actor="employee",
        event_type="software.request_created",
        outcome="success",
        request_id=request_id,
        entity_type="software_request",
        entity_id=software_request_id,
        mode="mock",
        details={"software": matched.name, "servicenow_number": sn_ref.number},
    )
    log_audit_event(
        db,
        actor="system",
        event_type="provisioning.started",
        outcome="success",
        request_id=request_id,
        entity_type="software_request",
        entity_id=software_request_id,
        mode="mock",
        details={"job_id": job_id},
    )

    # 3. Simulate completion & postcondition validation
    completed_at = _now()
    prov_ok = provisioner.validate_job(job_id)

    if prov_ok:
        updated_doc = update_request(
            db,
            software_request_id,
            {
                "status": SoftwareRequestStatus.completed.value,
                "provisioning.completed_at": completed_at,
                "provisioning.detail": f"Package {matched.name} {matched.version} successfully deployed (mock simulation).",
                "updated_at": completed_at,
            },
        )
        sn_client.update_service_request(
            db,
            sn_ref.sys_id,
            {"status": "closed_complete", "updated_at": completed_at},
        )
        log_audit_event(
            db,
            actor="system",
            event_type="provisioning.completed",
            outcome="success",
            request_id=request_id,
            entity_type="software_request",
            entity_id=software_request_id,
            mode="mock",
            details={"job_id": job_id, "status": "completed"},
        )
        final_doc = updated_doc or doc
    else:
        updated_doc = update_request(
            db,
            software_request_id,
            {
                "status": SoftwareRequestStatus.failed.value,
                "provisioning.detail": "Mock deployment failed validation.",
                "updated_at": completed_at,
            },
        )
        log_audit_event(
            db,
            actor="system",
            event_type="provisioning.failed",
            outcome="failure",
            request_id=request_id,
            entity_type="software_request",
            entity_id=software_request_id,
            mode="mock",
            details={"job_id": job_id},
        )
        final_doc = updated_doc or doc

    return SoftwareRequest(**final_doc)
