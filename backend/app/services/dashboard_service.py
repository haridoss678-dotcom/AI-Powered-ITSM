"""
Sorim.AI — Dashboard Service  (services/dashboard_service.py)

Calculates real aggregates from MongoDB collections matching API_CONTRACTS.md §9.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.core.config import get_settings
from app.repositories.automation_actions import count_actions_by_status, list_actions
from app.repositories.chat_history import list_chat_records
from app.repositories.software_requests import count_requests_by_status
from app.repositories.tickets import list_tickets
from app.schemas.dashboard import (
    DashboardAiSummary,
    DashboardAutomationSummary,
    DashboardSoftwareSummary,
    DashboardSummary,
    DashboardTicketsSummary,
)


def get_dashboard_summary(db: Any) -> DashboardSummary:
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    settings = get_settings()

    # 1. Tickets Aggregates
    # Load all tickets to ensure global aggregate is exact
    all_tickets, total_tickets = list_tickets(db, limit=1000)
    open_count = sum(1 for t in all_tickets if t.get("status") in {"open", "in_progress"})
    ai_resolved_count = sum(
        1 for t in all_tickets
        if t.get("status") in {"resolved", "closed"}
        and (t.get("resolution") or {}).get("type") == "automation"
    )
    escalated_count = sum(1 for t in all_tickets if t.get("escalated") is True)

    tickets_summary = DashboardTicketsSummary(
        total=total_tickets,
        open=open_count,
        ai_resolved=ai_resolved_count,
        escalated=escalated_count,
    )

    # 2. Software Requests Aggregates
    sw_counts = count_requests_by_status(db)
    sw_total = sum(sw_counts.values())
    software_summary = DashboardSoftwareSummary(
        total=sw_total,
        by_status=sw_counts,
    )

    # 3. Automation Actions Aggregates
    auto_counts = count_actions_by_status(db)
    auto_total = sum(auto_counts.values())
    recent_actions, _ = list_actions(db, limit=1)
    last_action_at = recent_actions[0].get("started_at") if recent_actions else None

    automation_summary = DashboardAutomationSummary(
        total_actions=auto_total,
        by_status=auto_counts,
        last_action_at=last_action_at,
    )

    # 4. AI Requests Total
    _, ai_total = list_chat_records(db, limit=1)
    ai_summary = DashboardAiSummary(total=ai_total)

    return DashboardSummary(
        generated_at=now_iso,
        servicenow_mode=settings.servicenow_mode,
        tickets=tickets_summary,
        software_requests=software_summary,
        automation=automation_summary,
        ai_requests=ai_summary,
    )
