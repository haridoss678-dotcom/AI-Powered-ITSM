"""
Sorim.AI — Automation Action Schemas  (schemas/automation.py)

Pydantic schemas matching API_CONTRACTS.md §1.7, §7 and DATA_MODEL.md §3.5.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import AutomationActionType, AutomationStatus


class AutomationStep(BaseModel):
    model_config = ConfigDict(extra="forbid")

    step: str
    status: Literal["completed", "failed", "skipped"]
    detail: str
    started_at: str
    finished_at: str | None = None


class AutomationEligibilityCheck(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    passed: bool
    detail: str


class AutomationEligibility(BaseModel):
    model_config = ConfigDict(extra="forbid")

    passed: bool
    checks: list[AutomationEligibilityCheck] = Field(default_factory=list)


class AutomationValidation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    passed: bool
    detail: str


class AutomationServiceNowUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["updated", "failed", "not_attempted"]
    detail: str


class AutomationAction(BaseModel):
    model_config = ConfigDict(extra="ignore")

    action_id: str
    request_id: str
    ticket_id: str | None = None
    employee_id: str
    action_type: AutomationActionType
    status: AutomationStatus
    mode: Literal["mock"] = "mock"
    eligibility: AutomationEligibility
    steps: list[AutomationStep] = Field(default_factory=list)
    validation: AutomationValidation | None = None
    servicenow_update: AutomationServiceNowUpdate
    started_at: str
    finished_at: str | None = None


class AutomationExecuteRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    employee_id: str = Field(min_length=1, max_length=32)
    action_type: AutomationActionType
    claim: str | None = Field(default=None, max_length=500)
