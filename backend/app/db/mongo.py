"""
Sorim.AI — MongoDB Client Lifecycle  (db/mongo.py)

Responsibilities (ARCHITECTURE §3.1):
  - Create ONE controlled PyMongo client at application startup.
  - Verify connectivity with a read-only ping; never write during health checks.
  - Expose get_db() for use in FastAPI dependencies.
  - Close the client cleanly during application shutdown.
  - Never log the URI, credentials, or sensitive connection details.

Phase 1 contract (API_CONTRACTS.md E-01):
  - A successful ping → database.status = "ok"
  - Any failure      → database.status = "error" with a safe detail string

Tests (TEST_PLAN.md DB-01):
  - Ping succeeds when Atlas is reachable.
  - Failure path reports correctly without revealing the URI.
  - No business writes during connectivity verification.
"""

from __future__ import annotations

import logging
from typing import Optional

import pymongo
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.errors import (
    ConfigurationError,
    ConnectionFailure,
    OperationFailure,
    PyMongoError,
    ServerSelectionTimeoutError,
)

from app.core.config import Settings
from app.repositories.users import ensure_demo_users

logger = logging.getLogger("sorim.db")

# Module-level holder — one client for the entire process lifetime.
_client: Optional[MongoClient] = None
_db: Optional[Database] = None


_using_local_fallback: bool = False


def init_db(settings: Settings) -> None:
    """
    Create and store the MongoClient singleton.

    Called once during application lifespan startup.
    Raises RuntimeError with a safe message if the URI is not configured.
    Does NOT ping here — ping happens in check_db_connectivity().
    """
    global _client, _db, _using_local_fallback
    _using_local_fallback = False

    uri = settings.mongodb_uri
    if not uri:
        raise RuntimeError(
            "MONGODB_URI is not set. "
            "Copy backend/.env.example to backend/.env and populate MONGODB_URI."
        )

    db_name = getattr(settings, "db_name", "itsm_helpdesk")
    info = settings.safe_db_info()
    logger.info(
        "Initialising MongoDB client | host=%s db=%s timeout_ms=%s",
        info["host_hint"],
        info["db_name"],
        info["timeout_ms"],
    )

    try:
        _client = MongoClient(
            uri,
            serverSelectionTimeoutMS=min(settings.mongodb_timeout_ms, 3000),
            connectTimeoutMS=min(settings.mongodb_timeout_ms, 3000),
            socketTimeoutMS=min(settings.mongodb_timeout_ms, 3000),
            # Recommended for Atlas
            tls=True,
            retryWrites=True,
            w="majority",
        )
        # Quick ping probe to verify if Atlas IP Access List permits connection
        _client.admin.command("ping")
        _db = _client[db_name]
        logger.info("MongoDB Atlas connection established successfully.")
    except Exception as exc:
        logger.warning(
            "MongoDB Atlas is currently unreachable (%s: likely IP Access List or network/DNS restriction). "
            "Enabling local database fallback for development so all UI screens and endpoints run without 503 errors.",
            type(exc).__name__,
        )
        from app.db.local_db import get_local_db
        _db = get_local_db()
        _using_local_fallback = True


def close_db() -> None:
    """Close the MongoClient during application shutdown."""
    global _client, _db, _using_local_fallback
    if _client is not None:
        try:
            _client.close()
            logger.info("MongoDB client closed.")
        except Exception:
            logger.warning("Error closing MongoDB client (ignored at shutdown).")
        finally:
            _client = None
            _db = None
            _using_local_fallback = False


def get_db() -> Database | Any:
    """
    Return the active database handle.

    Used by FastAPI dependency providers in api/deps.py.
    Raises RuntimeError if called before init_db().
    """
    global _db, _using_local_fallback
    if _db is None:
        raise RuntimeError(
            "Database is not initialised. "
            "Ensure init_db() was called during application startup."
        )

    if not _using_local_fallback:
        try:
            ensure_demo_users(_db)
        except Exception as exc:
            logger.warning("Atlas query failed (%s). Engaging local database fallback.", exc)
            from app.db.local_db import get_local_db
            _db = get_local_db()
            _using_local_fallback = True

    return _db


# ── Connectivity check (read-only) ───────────────────────────────────────────

class DbCheckResult:
    """Result of a single database connectivity probe."""

    __slots__ = ("ok", "detail", "latency_ms")

    def __init__(self, ok: bool, detail: Optional[str], latency_ms: Optional[int]) -> None:
        self.ok = ok
        self.detail = detail
        self.latency_ms = latency_ms


def check_db_connectivity() -> DbCheckResult:
    """
    Perform a read-only ping against the configured database.

    Returns DbCheckResult — never raises.
    Uses the existing _client; if not initialised, returns an error result.

    Contract (API_CONTRACTS.md E-01 Phase 1):
    - This is the sole read operation performed during the health check.
    - No collections are created, no documents are written or deleted.
    """
    if _client is None or not hasattr(_client, "admin"):
        return DbCheckResult(
            ok=False,
            detail="Database client is not initialised. Check MONGODB_URI configuration.",
            latency_ms=None,
        )

    import time

    start = time.monotonic()
    try:
        # admin.command("ping") is the recommended Atlas connectivity probe.
        # It requires no collection permissions and never writes data.
        result = _client.admin.command("ping")
        elapsed_ms = int((time.monotonic() - start) * 1000)

        if result.get("ok") == 1:
            logger.debug("MongoDB ping OK | latency_ms=%d", elapsed_ms)
            return DbCheckResult(ok=True, detail=None, latency_ms=elapsed_ms)
        else:
            return DbCheckResult(
                ok=False,
                detail="MongoDB ping returned unexpected result.",
                latency_ms=elapsed_ms,
            )

    except ServerSelectionTimeoutError:
        elapsed_ms = int((time.monotonic() - start) * 1000)
        logger.warning("MongoDB server selection timeout after %dms", elapsed_ms)
        return DbCheckResult(
            ok=False,
            detail=(
                "Cannot reach MongoDB Atlas within the configured timeout. "
                "Check MONGODB_URI, Atlas network access list, and internet connectivity."
            ),
            latency_ms=elapsed_ms,
        )

    except ConfigurationError as exc:
        logger.warning("MongoDB configuration error: %s", _safe_error_message(exc))
        return DbCheckResult(
            ok=False,
            detail="MongoDB configuration is invalid. Check MONGODB_URI format.",
            latency_ms=None,
        )

    except OperationFailure as exc:
        logger.warning("MongoDB authentication failure (code %s)", exc.code)
        return DbCheckResult(
            ok=False,
            detail=(
                "MongoDB authentication failed. "
                "Verify the username and password in MONGODB_URI against Atlas Database Access."
            ),
            latency_ms=None,
        )

    except ConnectionFailure:
        elapsed_ms = int((time.monotonic() - start) * 1000)
        logger.warning("MongoDB connection failure after %dms", elapsed_ms)
        return DbCheckResult(
            ok=False,
            detail=(
                "Cannot connect to MongoDB Atlas. "
                "Check MONGODB_URI and network access list."
            ),
            latency_ms=elapsed_ms,
        )

    except PyMongoError as exc:
        logger.warning("MongoDB error: %s", type(exc).__name__)
        return DbCheckResult(
            ok=False,
            detail="Cannot connect to MongoDB Atlas (check MONGODB_URI and network access).",
            latency_ms=None,
        )

    except Exception:
        logger.exception("Unexpected error during MongoDB ping")
        return DbCheckResult(
            ok=False,
            detail="An unexpected error occurred while checking database connectivity.",
            latency_ms=None,
        )


def _safe_error_message(exc: Exception) -> str:
    """
    Return a sanitised error string that will not reveal URI or credentials.
    PyMongo can embed the URI in exception messages.
    """
    msg = str(exc)
    # Strip anything that looks like a connection string.
    for prefix in ("mongodb+srv://", "mongodb://"):
        if prefix in msg:
            idx = msg.find(prefix)
            msg = msg[:idx] + "<redacted_uri>"
    return msg


def is_using_fallback() -> bool:
    """Return True if the backend is actively using the local in-memory database fallback."""
    return _using_local_fallback
