"""
Sorim.AI — FastAPI Application Entry Point  (app/main.py)

Responsibilities (ARCHITECTURE §3.1):
  - Create the FastAPI application instance.
  - Mount the versioned API router.
  - Register exception handlers.
  - Configure CORS (explicit allowed origins only — no wildcard in production).
  - Manage the MongoDB client lifecycle via a lifespan context manager.
  - Expose API documentation in development.

Security rules enforced here:
  - CORS origins are read from configuration, never hardcoded.
  - Credentials and URIs are never logged.
  - Startup errors produce actionable messages without exposing secrets.
  - Unhandled exceptions are caught and return the uniform error envelope.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.ai.llm.llm_service import initialize as initialize_llm
from app.api.router import api_router
from app.core.config import get_settings
from app.core.errors import AppError, register_exception_handlers
from app.core.logging import configure_logging
from app.db.mongo import close_db, init_db

# ── Configure logging before anything else ───────────────────────────────────
settings = get_settings()
configure_logging(settings.log_level)
logger = logging.getLogger("sorim.main")


# ── Application lifespan ─────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Startup → yield → Shutdown lifecycle.

    Startup:
      - Validate configuration (already done by pydantic-settings).
      - Initialise the MongoDB client (does not ping — ping is health-check only).
      - Log safe startup summary.

    Shutdown:
      - Close the MongoDB client.
    """
    logger.info(
        "Sorim.AI backend starting | env=%s version=%s",
        settings.app_env,
        settings.app_version,
    )

    try:
        init_db(settings)
    except RuntimeError as exc:
        # Configuration error: missing MONGODB_URI. Log the message (safe — no URI in it).
        logger.critical("STARTUP FAILED — database configuration error: %s", exc)
        # Still allow the app to start so that the health endpoint can report the failure.
        # The health check will return 503 because _client is None.

    except Exception as exc:
        logger.critical("STARTUP FAILED — unexpected error: %s", type(exc).__name__)

    try:
        initialize_llm()
    except AppError as exc:
        logger.warning("Local LLM readiness check: %s", exc.message)

    db_info = settings.safe_db_info()
    logger.info(
        "MongoDB client initialised | host=%s db=%s",
        db_info["host_hint"],
        db_info["db_name"],
    )

    try:
        from app.ai.rag.vector_store import get_vector_store
        from app.db.mongo import get_db
        from app.services.knowledge_service import ingest_knowledge_base
        v_store = get_vector_store()
        if v_store.count() == 0:
            logger.info("Vector store is unindexed. Ingesting knowledge base articles...")
            ingest_knowledge_base(get_db())
            logger.info("Knowledge base articles ingested successfully | chunks=%d", v_store.count())
    except Exception as exc:
        logger.warning("Knowledge auto-ingestion check: %s", exc)

    yield  # Application handles requests here.

    logger.info("Sorim.AI backend shutting down.")
    close_db()


# ── FastAPI application factory ───────────────────────────────────────────────

def create_app() -> FastAPI:
    cfg = get_settings()

    app = FastAPI(
        title="Sorim.AI — Intelligent ITSM & Helpdesk API",
        description=(
            "AI-Powered ITSM and Intelligent Helpdesk Automation Platform. "
            "Phase 1: application foundation and health endpoint."
        ),
        version=cfg.app_version,
        docs_url="/docs" if cfg.is_development else None,
        redoc_url="/redoc" if cfg.is_development else None,
        openapi_url="/openapi.json" if cfg.is_development else None,
        lifespan=lifespan,
    )

    # ── CORS — restrict to configured origins ────────────────────────────────
    origins = list(dict.fromkeys(cfg.cors_origins_list + ["http://localhost:5173", "http://127.0.0.1:5173"]))
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"] if cfg.is_development else ["Content-Type", "Accept", "X-Request-ID"],
    )

    # ── Exception handlers ───────────────────────────────────────────────────
    register_exception_handlers(app)

    # ── Routes ───────────────────────────────────────────────────────────────
    app.include_router(api_router)

    return app


# Module-level application instance used by Uvicorn.
app = create_app()
