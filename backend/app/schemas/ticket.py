from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.common import Impact, Priority, TicketSource, TicketStatus, Urgency


class ServiceNowRef(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mode: Literal["mock"] = "mock"
    record_type: Literal["incident"] = "incident"
    number: str
    sys_id: str


class TicketWorkNote(BaseModel):
    model_config = ConfigDict(extra="forbid")

    timestamp: str
    actor: str
    text: str


class Resolution(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["automation", "human"]
    resolved_at: str
    notes: Optional[str] = None


class TicketRecord(BaseModel):
    model_config = ConfigDict(extra="ignore")

    ticket_id: str
    status: TicketStatus
    source: TicketSource
    requester: dict[str, str]
    short_description: str = Field(..., min_length=1, max_length=160)
    description: str = Field(..., min_length=1, max_length=2000)
    intent: Literal["incident"] = "incident"
    category: str
    subcategory: str
    priority: Priority
    impact: Impact
    urgency: Urgency
    assignment_group: str
    suggested_resolution: Optional[str] = None
    escalated: bool = False
    escalation_reason: Optional[str] = None
    resolution: Optional[Resolution] = None
    servicenow_ref: ServiceNowRef
    request_id: Optional[str] = None
    automation_action_id: Optional[str] = None
    work_notes: list[TicketWorkNote] = Field(default_factory=list)
    created_at: str
    updated_at: str


class TicketCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    employee_id: str
    confirmed: bool = False
    request_id: Optional[str] = None
    short_description: Optional[str] = None
    description: Optional[str] = None

    @model_validator(mode="after")
    def validate_payload(self) -> "TicketCreateRequest":
        if not self.confirmed:
            raise ValueError("Employee confirmation is required before creating a ticket.")

        if self.request_id is not None:
            if self.short_description is not None or self.description is not None:
                raise ValueError("request_id cannot be combined with manual ticket fields.")
            return self

        if not self.short_description or not self.description:
            raise ValueError("Manual ticket creation requires short_description and description.")
        if len(self.short_description.strip()) < 1 or len(self.short_description.strip()) > 160:
            raise ValueError("short_description must be 1-160 characters.")
        if len(self.description.strip()) < 1 or len(self.description.strip()) > 2000:
            raise ValueError("description must be 1-2000 characters.")
        return self


class TicketUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Optional[TicketStatus] = None
    work_note: Optional[str] = None

    @model_validator(mode="after")
    def validate_update(self) -> "TicketUpdateRequest":
        if self.status is None and (self.work_note is None or not self.work_note.strip()):
            raise ValueError("Provide at least one valid field: status or work_note.")
        if self.work_note is not None:
            if not self.work_note.strip():
                raise ValueError("work_note must contain non-whitespace text when provided.")
            if len(self.work_note.strip()) > 1000:
                raise ValueError("work_note must be <= 1000 characters.")
        return self


class TicketListQuery(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Optional[TicketStatus] = None
    escalated: Optional[bool] = None
    employee_id: Optional[str] = None
    limit: int = 50
    skip: int = 0

    @model_validator(mode="after")
    def validate_query(self) -> "TicketListQuery":
        if self.limit < 1 or self.limit > 200:
            raise ValueError("limit must be between 1 and 200.")
        if self.skip < 0:
            raise ValueError("skip must be >= 0.")
        return self


def make_ticket_id(seed: int) -> str:
    return f"TKT-{seed:06d}"


def make_servicenow_number(seed: int) -> str:
    return f"INC{seed:06d}"


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
