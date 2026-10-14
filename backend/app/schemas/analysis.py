from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.schemas.common import (
    AutomationActionType,
    EscalationReason,
    Impact,
    Intent,
    Outcome,
    Priority,
    Urgency,
)


class AnalysisRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    employee_id: str = Field(min_length=1, max_length=32)
    message: str = Field(min_length=1, max_length=2000)

    @field_validator("employee_id", "message")
    @classmethod
    def trim_required_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be blank")
        return value


class AnalysisSignals(BaseModel):
    model_config = ConfigDict(extra="forbid")

    llm_impact: Impact | None
    llm_urgency: Urgency | None
    impact_rule_hit: str | None
    urgency_rule_hit: str | None


class Analysis(BaseModel):
    model_config = ConfigDict(extra="forbid")

    intent: Intent
    category: str
    subcategory: str
    priority: Priority | None
    impact: Impact | None
    urgency: Urgency | None
    assignment_group: str | None
    summary: str = Field(min_length=1, max_length=160)
    suggested_resolution: str | None = Field(default=None, max_length=200)
    automation_action_type: AutomationActionType | None = None
    software_name: str | None = Field(default=None, max_length=100)
    signals: AnalysisSignals
    llm_attempts: int = Field(ge=1, le=2)
    model_id: str

    @model_validator(mode="after")
    def validate_intent_fields(self) -> Analysis:
        if self.intent in {Intent.incident, Intent.automatable_issue}:
            if self.priority is None or self.impact is None or self.urgency is None:
                raise ValueError("priority, impact, and urgency are required for this intent")
        elif any(value is not None for value in (self.priority, self.impact, self.urgency)):
            raise ValueError("priority, impact, and urgency must be null for this intent")

        if self.intent == Intent.knowledge_question:
            if self.assignment_group is not None:
                raise ValueError("assignment_group must be null for knowledge questions")
        elif self.assignment_group is None:
            raise ValueError("assignment_group is required for this intent")

        if (self.intent == Intent.automatable_issue) != (self.automation_action_type is not None):
            raise ValueError("automation_action_type is required only for automatable issues")
        if (self.intent == Intent.service_request) != (self.software_name is not None):
            raise ValueError("software_name is required only for service requests")
        return self


class ConfidenceComponents(BaseModel):
    model_config = ConfigDict(extra="forbid")

    classification_agreement: float | None = Field(default=None, ge=0, le=1)
    retrieval_top_score: float | None = Field(default=None, ge=0, le=1)
    grounding_score: float | None = Field(default=None, ge=0, le=1)


class Confidence(BaseModel):
    model_config = ConfigDict(extra="forbid")

    score: float = Field(ge=0, le=1)
    level: Literal["high", "medium", "low"]
    threshold: float = Field(ge=0, le=1)
    below_threshold: bool
    method: Literal["heuristic_v1"] = "heuristic_v1"
    components: ConfidenceComponents
    note: Literal["Heuristic score, not a calibrated probability"] = (
        "Heuristic score, not a calibrated probability"
    )


class Escalation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    required: bool
    reason: EscalationReason | None
    message: str | None
    ticket_option_available: bool


class Timings(BaseModel):
    model_config = ConfigDict(extra="forbid")

    analysis: int | None
    retrieval: int | None
    generation: int | None
    total: int | None


class ChatRecord(BaseModel):
    model_config = ConfigDict(extra="ignore")

    request_id: str
    entry_type: Literal["chat", "analysis"]
    conversation_id: str | None = None
    employee_id: str
    message: str
    analysis: Analysis | None = None
    answer: str | None = None
    sources: list[dict] = Field(default_factory=list)
    confidence: Confidence | None = None
    outcome: Outcome
    escalation: Escalation
    ticket_id: str | None = None
    automation_action_id: str | None = None
    software_request_id: str | None = None
    ticket: dict | None = None
    automation: dict | None = None
    software_request: dict | None = None
    timings_ms: Timings
    llm_model_id: str
    created_at: str


class AnalysisModelOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    intent: Intent
    category: str
    subcategory: str
    impact: Impact | None = None
    urgency: Urgency | None = None
    summary: str = Field(min_length=1, max_length=160)
    suggested_resolution: str | None = Field(default=None, max_length=200)
    automation_action_type: AutomationActionType | None = None
    software_name: str | None = Field(default=None, max_length=100)

    @model_validator(mode="after")
    def validate_model_output_fields(self) -> AnalysisModelOutput:
        if self.intent in {Intent.incident, Intent.automatable_issue}:
            if self.impact is None or self.urgency is None:
                raise ValueError("impact and urgency are required for this intent")
        elif self.impact is not None or self.urgency is not None:
            raise ValueError("impact and urgency must be null for this intent")
        if (self.intent == Intent.automatable_issue) != (self.automation_action_type is not None):
            raise ValueError("automation_action_type does not match intent")
        if (self.intent == Intent.service_request) != (self.software_name is not None):
            raise ValueError("software_name does not match intent")
        return self
