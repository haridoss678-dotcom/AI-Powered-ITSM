"""
Sorim.AI — Software Request & Catalogue Routes  (api/routes/software_requests.py)

Implements E-15, E-16, E-17 and catalogue listing per API_CONTRACTS.md §8.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_db
from app.core.errors import AppError, ErrorCode
from app.repositories.software_requests import get_request, list_requests
from app.schemas.common import Page
from app.schemas.software import (
    SoftwareCatalogueItem,
    SoftwareRequest,
    SoftwareRequestCreate,
)
from app.services import software_catalogue
from app.workflows.provisioning import handle_software_request

router = APIRouter(tags=["software"])


@router.post(
    "/software-requests",
    response_model=SoftwareRequest,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a software provisioning request",
)
def create_software_request(
    payload: SoftwareRequestCreate,
    db: Any = Depends(get_db),
) -> SoftwareRequest:
    return handle_software_request(
        db,
        employee_id=payload.employee_id,
        software_name=payload.software_name,
        request_id=payload.request_id,
    )


@router.get(
    "/software-requests",
    response_model=Page[SoftwareRequest],
    summary="List software provisioning requests",
)
def get_software_requests(
    status: str | None = Query(default=None),
    employee_id: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    skip: int = Query(default=0, ge=0),
    db: Any = Depends(get_db),
) -> Page[SoftwareRequest]:
    items, total = list_requests(db, status=status, employee_id=employee_id, skip=skip, limit=limit)
    return Page(
        items=[SoftwareRequest(**it) for it in items],
        total=total,
        limit=limit,
        skip=skip,
    )


@router.get(
    "/software-requests/{software_request_id}",
    response_model=SoftwareRequest,
    summary="Get single software request status",
)
def get_single_software_request(
    software_request_id: str,
    db: Any = Depends(get_db),
) -> SoftwareRequest:
    record = get_request(db, software_request_id)
    if record is None:
        raise AppError(
            code=ErrorCode.NOT_FOUND,
            message=f"Software request '{software_request_id}' was not found.",
            http_status=404,
        )
    return SoftwareRequest(**record)


@router.get(
    "/software/catalogue",
    response_model=list[SoftwareCatalogueItem],
    summary="List available items in corporate software catalogue",
)
def get_catalogue() -> list[SoftwareCatalogueItem]:
    return software_catalogue.list_catalogue()


@router.get(
    "/software/catalogue/{item_id}",
    response_model=SoftwareCatalogueItem,
    summary="Get catalogue item details",
)
def get_catalogue_details(item_id: str) -> SoftwareCatalogueItem:
    item = software_catalogue.get_catalogue_item(item_id)
    if item is None:
        raise AppError(
            code=ErrorCode.NOT_FOUND,
            message=f"Catalogue item '{item_id}' was not found.",
            http_status=404,
        )
    return item
