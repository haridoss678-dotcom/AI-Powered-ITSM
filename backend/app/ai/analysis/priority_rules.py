from __future__ import annotations

from app.schemas.common import Impact, Priority, Urgency


PRIORITY_MATRIX = {
    (Impact.organization, Urgency.high): Priority.P1,
    (Impact.organization, Urgency.medium): Priority.P1,
    (Impact.organization, Urgency.low): Priority.P2,
    (Impact.group, Urgency.high): Priority.P1,
    (Impact.group, Urgency.medium): Priority.P2,
    (Impact.group, Urgency.low): Priority.P3,
    (Impact.individual, Urgency.high): Priority.P2,
    (Impact.individual, Urgency.medium): Priority.P3,
    (Impact.individual, Urgency.low): Priority.P4,
}

_ORGANIZATION_IMPACT = ("company-wide", "all employees", "whole company")
_GROUP_IMPACT = ("everyone", "whole team", "all users", "entire department")
_HIGH_URGENCY = ("cannot", "can't", "unable", "keeps failing", "not working", "blocked", "urgent")
_LOW_URGENCY = ("no rush", "when you get a chance", "minor")


def derive_impact(message: str, proposed: Impact) -> tuple[Impact, str | None]:
    text = message.casefold()
    for phrase in _ORGANIZATION_IMPACT:
        if phrase in text:
            return Impact.organization, phrase
    for phrase in _GROUP_IMPACT:
        if phrase in text:
            return Impact.group, phrase
    return proposed, None


def derive_urgency(message: str, proposed: Urgency) -> tuple[Urgency, str | None]:
    text = message.casefold()
    for phrase in _HIGH_URGENCY:
        if phrase in text:
            return Urgency.high, phrase
    for phrase in _LOW_URGENCY:
        if phrase in text:
            return Urgency.low, phrase
    return proposed, None


def derive_priority(impact: Impact, urgency: Urgency) -> Priority:
    return PRIORITY_MATRIX[(impact, urgency)]
