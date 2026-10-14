from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_db
from app.core.errors import AppError, ErrorCode
from app.schemas.common import Page
from app.schemas.ticket import TicketCreateRequest, TicketRecord, TicketUpdateRequest
from app.services.ticket_service import create_ticket, get_ticket_by_id, list_ticket_records, update_ticket_record

router = APIRouter(prefix="/tickets", tags=["tickets"])


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=TicketRecord,
)
async def create_ticket_route(payload: TicketCreateRequest, db=Depends(get_db)):
    return create_ticket(db, payload.model_dump())


@router.get("", response_model=Page[TicketRecord])
async def list_tickets_route(
    db=Depends(get_db),
    status_filter: str | None = Query(default=None, alias="status"),
    escalated: bool | None = None,
    employee_id: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    skip: int = Query(default=0, ge=0),
):
    return list_ticket_records(
        db,
        status=status_filter,
        escalated=escalated,
        employee_id=employee_id,
        skip=skip,
        limit=limit,
    )


@router.get("/{ticket_id}", response_model=TicketRecord)
async def get_ticket_route(ticket_id: str, db=Depends(get_db)):
    return get_ticket_by_id(db, ticket_id)


@router.patch("/{ticket_id}", response_model=TicketRecord)
async def update_ticket_route(ticket_id: str, payload: TicketUpdateRequest, db=Depends(get_db)):
    return update_ticket_record(db, ticket_id, payload.model_dump(exclude_none=True))
