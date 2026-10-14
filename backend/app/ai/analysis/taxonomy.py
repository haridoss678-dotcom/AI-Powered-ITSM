from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TaxonomyEntry:
    category: str
    subcategory: str
    assignment_group: str
    keywords: tuple[str, ...]


TAXONOMY = (
    TaxonomyEntry("Network", "VPN", "Network Support", ("vpn", "authentication")),
    TaxonomyEntry("Network", "Wi-Fi", "Network Support", ("wi-fi", "wifi", "wireless")),
    TaxonomyEntry(
        "Identity & Access",
        "Password Reset",
        "Identity & Access Support",
        ("password", "expired"),
    ),
    TaxonomyEntry(
        "Identity & Access",
        "Account Lockout",
        "Identity & Access Support",
        ("locked out", "account lockout"),
    ),
    TaxonomyEntry(
        "Identity & Access",
        "Application Access",
        "Application Support",
        ("application access", "permission"),
    ),
    TaxonomyEntry(
        "Email & Collaboration",
        "Outlook",
        "Messaging Support",
        ("outlook", "synchronization", "sync"),
    ),
    TaxonomyEntry(
        "Hardware",
        "Laptop Performance",
        "Desktop Support",
        ("laptop", "slow", "performance"),
    ),
    TaxonomyEntry(
        "Software",
        "Installation",
        "Desktop Support",
        ("install", "installation", "software"),
    ),
    TaxonomyEntry("Other", "Uncategorized", "Service Desk", ()),
)


def find_entry(category: str, subcategory: str) -> TaxonomyEntry | None:
    return next(
        (
            entry
            for entry in TAXONOMY
            if entry.category.casefold() == category.casefold()
            and entry.subcategory.casefold() == subcategory.casefold()
        ),
        None,
    )


def assignment_group(category: str, subcategory: str) -> str:
    entry = find_entry(category, subcategory)
    if entry is None:
        raise ValueError(f"Unsupported category/subcategory pair: {category}/{subcategory}")
    return entry.assignment_group


def classification_agreement(message: str, category: str, subcategory: str) -> float:
    text = message.casefold()
    evidenced = [
        entry
        for entry in TAXONOMY
        if entry.keywords and any(keyword in text for keyword in entry.keywords)
    ]
    if not evidenced:
        return 0.5
    return 1.0 if any(
        entry.category.casefold() == category.casefold()
        and entry.subcategory.casefold() == subcategory.casefold()
        for entry in evidenced
    ) else 0.0
