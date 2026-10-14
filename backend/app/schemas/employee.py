from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, Field, field_validator
import re

_EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

AccountStatus = Literal["active", "locked", "password_expired"]


class MockAccount(BaseModel):
    account_status: AccountStatus = "active"
    privileged: bool = False


class EmployeeCreateRequest(BaseModel):
    employee_id: str | None = Field(
        default=None,
        description="Optional employee ID (e.g. EMP-004). If omitted, a unique ID is safely auto-generated.",
    )
    name: str = Field(..., min_length=2, max_length=100)
    email: str = Field(..., min_length=5, max_length=100)
    department: str = Field(..., min_length=2, max_length=50)
    account_status: AccountStatus = Field(default="active")
    privileged: bool = Field(default=False, description="Whether employee has domain admin / privileged IT role")

    @field_validator("name", "department")
    @classmethod
    def not_empty_str(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("Field cannot be empty or whitespace.")
        return s

    @field_validator("email")
    @classmethod
    def validate_email_format(cls, v: str) -> str:
        s = v.strip().lower()
        if not _EMAIL_REGEX.match(s):
            raise ValueError("Invalid email format.")
        return s

    @field_validator("employee_id")
    @classmethod
    def validate_employee_id(cls, v: str | None) -> str | None:
        if v is None:
            return None
        s = v.strip().upper()
        if not s:
            return None
        if not s.startswith("EMP-"):
            raise ValueError("Employee ID must follow standard corporate format starting with 'EMP-'.")
        return s


class EmployeeRecord(BaseModel):
    employee_id: str
    name: str
    email: str
    department: str
    mock_account: MockAccount
    created_at: str
