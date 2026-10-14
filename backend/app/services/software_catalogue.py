"""
Sorim.AI — Software Catalogue Service  (services/software_catalogue.py)

Manages lookup and matching against data/software_catalogue.json.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.schemas.software import SoftwareCatalogueItem

_CATALOGUE_PATH = Path(__file__).resolve().parents[3] / "data" / "software_catalogue.json"


def _load_catalogue_data() -> list[dict[str, Any]]:
    if not _CATALOGUE_PATH.is_file():
        return []
    try:
        return json.loads(_CATALOGUE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return []


def list_catalogue() -> list[SoftwareCatalogueItem]:
    raw = _load_catalogue_data()
    return [SoftwareCatalogueItem(**it) for it in raw]


def get_catalogue_item(identifier: str) -> SoftwareCatalogueItem | None:
    raw = _load_catalogue_data()
    ident_lower = identifier.strip().lower()
    for item in raw:
        if item["catalogue_id"].lower() == ident_lower or item["name"].lower() == ident_lower:
            return SoftwareCatalogueItem(**item)
    return None


def match_software(query: str) -> SoftwareCatalogueItem | None:
    raw = _load_catalogue_data()
    q = query.strip().lower()

    # 1. Exact name or id match
    for item in raw:
        if item["catalogue_id"].lower() == q or item["name"].lower() == q:
            return SoftwareCatalogueItem(**item)

    # 2. Alias match
    for item in raw:
        for alias in item.get("aliases", []):
            if alias.lower() == q:
                return SoftwareCatalogueItem(**item)

    # 3. Substring / keyword match
    for item in raw:
        if item["name"].lower() in q:
            return SoftwareCatalogueItem(**item)
        for alias in item.get("aliases", []):
            if alias.lower() in q:
                return SoftwareCatalogueItem(**item)

    return None
