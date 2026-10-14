from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, status

from app.api.deps import get_db
from app.core.errors import AppError, ErrorCode
from app.repositories.sequences import get_next_sequence
from app.repositories.users import ensure_demo_users, get_user, insert_user, list_users
from app.schemas.employee import EmployeeCreateRequest, EmployeeRecord, MockAccount
from app.services.audit_service import log_audit_event

router = APIRouter(prefix="/employees", tags=["employees"])


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _to_record(doc: dict[str, Any]) -> EmployeeRecord:
    mock_acc = doc.get("mock_account") or {}
    return EmployeeRecord(
        employee_id=doc.get("_id", doc.get("employee_id", "")),
        name=doc.get("name", "Unknown"),
        email=doc.get("email", ""),
        department=doc.get("department", "General"),
        mock_account=MockAccount(
            account_status=mock_acc.get("account_status", "active"),
            privileged=bool(mock_acc.get("privileged", False)),
        ),
        created_at=str(doc.get("created_at", _now_iso())),
    )


@router.get("", response_model=list[EmployeeRecord], summary="List all employees from corporate directory")
def list_employees_route(db: Any = Depends(get_db)) -> list[EmployeeRecord]:
    users = list_users(db)
    return [_to_record(u) for u in users]


@router.get("/{employee_id}", response_model=EmployeeRecord, summary="Retrieve canonical employee profile by ID")
def get_employee_route(employee_id: str, db: Any = Depends(get_db)) -> EmployeeRecord:
    user = get_user(db, employee_id.strip().upper())
    if user is None:
        raise AppError(
            code=ErrorCode.EMPLOYEE_NOT_FOUND,
            message=f"Employee '{employee_id}' was not found in directory.",
            http_status=status.HTTP_404_NOT_FOUND,
        )
    return _to_record(user)


@router.post(
    "",
    response_model=EmployeeRecord,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new corporate employee in the directory",
)
def create_employee_route(
    payload: EmployeeCreateRequest,
    db: Any = Depends(get_db),
) -> EmployeeRecord:
    ensure_demo_users(db)
    emp_id = payload.employee_id
    if emp_id:
        emp_id = emp_id.strip().upper()
        existing = get_user(db, emp_id)
        if existing is not None:
            raise AppError(
                code=ErrorCode.CONFLICT,
                message=f"Employee ID '{emp_id}' is already registered.",
                http_status=status.HTTP_409_CONFLICT,
            )
    else:
        seq = get_next_sequence(db, "employee")
        emp_id = f"EMP-{seq:03d}"
        while get_user(db, emp_id) is not None:
            seq = get_next_sequence(db, "employee")
            emp_id = f"EMP-{seq:03d}"

    now = _now_iso()
    user_doc = {
        "_id": emp_id,
        "name": payload.name.strip(),
        "email": str(payload.email).strip().lower(),
        "department": payload.department.strip(),
        "mock_account": {
            "account_status": payload.account_status,
            "privileged": payload.privileged,
        },
        "created_at": now,
    }

    insert_user(db, user_doc)
    log_audit_event(
        db,
        actor="admin",
        event_type="employee.created",
        outcome="success",
        entity_type="user",
        entity_id=emp_id,
        details={
            "department": payload.department,
            "privileged": payload.privileged,
            "status": payload.account_status,
        },
        mode=None,
    )
    return _to_record(user_doc)
