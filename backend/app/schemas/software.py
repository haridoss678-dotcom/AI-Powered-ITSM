"""
Sorim.AI — Software Catalogue & Provisioning Schemas  (schemas/software.py)

Pydantic schemas matching API_CONTRACTS.md §1.8, §8 and DATA_MODEL.md §3.6.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import SoftwareRequestStatus


class SoftwareCatalogueItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    catalogue_id: str
    name: str
    aliases: list[str] = Field(default_factory=list)
    version: str
    category: str
    description: str


class SoftwareSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid")

    catalogue_id: str
    name: str
    version: str


class EmployeeSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid")

    employee_id: str
    name: str


class ProvisioningInfo(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mode: Literal["mock"] = "mock"
    job_id: str
    detail: str
    started_at: str
    completed_at: str | None = None


class SoftwareServiceNowRef(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mode: Literal["mock"] = "mock"
    record_type: Literal["service_request"] = "service_request"
    number: str
    sys_id: str


class SoftwareRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    software_request_id: str
    employee: EmployeeSnapshot
    software: SoftwareSnapshot
    status: SoftwareRequestStatus
    servicenow_ref: SoftwareServiceNowRef
    provisioning: ProvisioningInfo
    request_id: str | None = None
    created_at: str
    updated_at: str


class SoftwareRequestCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    employee_id: str = Field(min_length=1, max_length=32)
    software_name: str = Field(min_length=1, max_length=100)
    request_id: str | None = None
