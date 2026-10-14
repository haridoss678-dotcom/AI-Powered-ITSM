"""
Sorim.AI — Dashboard Summary Schemas  (schemas/dashboard.py)

Pydantic schemas matching API_CONTRACTS.md §1.12, §9 and DATA_MODEL.md.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class DashboardTicketsSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total: int
    open: int
    ai_resolved: int
    escalated: int


class DashboardSoftwareSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total: int
    by_status: dict[str, int] = Field(default_factory=dict)


class DashboardAutomationSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total_actions: int
    by_status: dict[str, int] = Field(default_factory=dict)
    last_action_at: str | None = None


class DashboardAiSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total: int


class DashboardSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    generated_at: str
    servicenow_mode: str
    tickets: DashboardTicketsSummary
    software_requests: DashboardSoftwareSummary
    automation: DashboardAutomationSummary
    ai_requests: DashboardAiSummary
