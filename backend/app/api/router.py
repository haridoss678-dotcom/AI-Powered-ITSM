"""
Sorim.AI — API Router  (api/router.py)

Aggregates all route modules under the /api/v1 prefix matching API_CONTRACTS.md.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.api.routes import (
    analysis,
    audit,
    automation,
    chat,
    dashboard,
    employees,
    health,
    knowledge,
    software_requests,
    tickets,
)

api_router = APIRouter(prefix="/api/v1")

# Registered routes for all application workflows
api_router.include_router(health.router)
api_router.include_router(employees.router)
api_router.include_router(tickets.router)
api_router.include_router(analysis.router)
api_router.include_router(knowledge.router)
api_router.include_router(chat.router)
api_router.include_router(automation.router)
api_router.include_router(audit.router)
api_router.include_router(software_requests.router)
api_router.include_router(dashboard.router)
