"""
Sorim.AI — Common Shared Schemas  (schemas/common.py)

Reusable Pydantic models shared across multiple endpoints.
Enums match DATA_MODEL.md §5 exactly.
"""

from __future__ import annotations

from enum import Enum
from typing import Generic, List, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


# ── Pagination wrapper (API_CONTRACTS.md §0) ─────────────────────────────────

class Page(BaseModel, Generic[T]):
    items: List[T]
    total: int
    limit: int
    skip: int


# ── Enumerations (DATA_MODEL.md §5 — locked) ─────────────────────────────────

class Intent(str, Enum):
    knowledge_question = "knowledge_question"
    incident = "incident"
    service_request = "service_request"
    automatable_issue = "automatable_issue"


class Impact(str, Enum):
    individual = "individual"
    group = "group"
    organization = "organization"


class Urgency(str, Enum):
    high = "high"
    medium = "medium"
    low = "low"


class Priority(str, Enum):
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"
    P4 = "P4"


class TicketStatus(str, Enum):
    open = "open"
    in_progress = "in_progress"
    resolved = "resolved"
    closed = "closed"


class TicketSource(str, Enum):
    chat_analysis = "chat_analysis"
    manual = "manual"
    self_heal = "self_heal"


class ResolutionType(str, Enum):
    automation = "automation"
    human = "human"


class Outcome(str, Enum):
    answered = "answered"
    insufficient_knowledge = "insufficient_knowledge"
    ticket_suggested = "ticket_suggested"
    ticket_created = "ticket_created"
    software_request_created = "software_request_created"
    software_not_available = "software_not_available"
    automation_resolved = "automation_resolved"
    automation_escalated = "automation_escalated"
    analysis_failed = "analysis_failed"
    analysis_only = "analysis_only"


class EscalationReason(str, Enum):
    insufficient_knowledge = "insufficient_knowledge"
    low_confidence = "low_confidence"
    analysis_failed = "analysis_failed"
    automation_failed = "automation_failed"
    automation_ineligible = "automation_ineligible"
    software_not_available = "software_not_available"


class AutomationActionType(str, Enum):
    password_reset = "password_reset"
    account_unlock = "account_unlock"
    service_restart = "service_restart"
    cache_clearing = "cache_clearing"
    vpn_status_check = "vpn_status_check"
    application_restart = "application_restart"


class AutomationStatus(str, Enum):
    succeeded = "succeeded"
    failed = "failed"
    validation_failed = "validation_failed"
    skipped_ineligible = "skipped_ineligible"


class SoftwareRequestStatus(str, Enum):
    submitted = "submitted"
    provisioning = "provisioning"
    completed = "completed"
    failed = "failed"


class ServiceNowMode(str, Enum):
    mock = "mock"
    live = "live"


class HealthCheckStatus(str, Enum):
    ok = "ok"
    error = "error"
    not_configured = "not_configured"


class AuditOutcome(str, Enum):
    success = "success"
    failure = "failure"


class Actor(str, Enum):
    employee = "employee"
    ai = "ai"
    system = "system"
    automation = "automation"
