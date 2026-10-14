"""
Sorim.AI — Escalation Decision Logic  (ai/safety/escalation.py)

Manages safe escalation and human handoff triggers.
"""

from __future__ import annotations

from app.schemas.analysis import Escalation
from app.schemas.common import EscalationReason


def determine_escalation(
    *,
    required: bool,
    reason: EscalationReason | None = None,
    message: str | None = None,
    ticket_option_available: bool = True,
) -> Escalation:
    return Escalation(
        required=required,
        reason=reason,
        message=message,
        ticket_option_available=ticket_option_available,
    )
