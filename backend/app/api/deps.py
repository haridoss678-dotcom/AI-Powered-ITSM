"""
Sorim.AI — FastAPI Dependencies  (api/deps.py)

Provides injectable dependencies for routes:
  - get_db()    → active MongoDB database handle
  - get_settings() → application settings

In tests, these can be overridden with app.dependency_overrides.
Future phases will add: get_servicenow_client, get_llm_service, etc.
"""

from __future__ import annotations

from typing import Generator

from fastapi import Depends
from pymongo.database import Database
from pymongo.errors import PyMongoError

from app.core.config import Settings, get_settings as _get_settings
from app.db.mongo import get_db as _get_db


def get_settings() -> Settings:
    """Dependency: return the application settings singleton."""
    return _get_settings()


def get_db(
    settings: Settings = Depends(get_settings),
) -> Generator[Database, None, None]:
    """
    Dependency: yield the active MongoDB database handle.

    Raises 503 AppError if the database is not available.
    Tests can override this via app.dependency_overrides[get_db].
    """
    from app.core.errors import AppError, ErrorCode
    from fastapi import status

    try:
        db = _get_db()
        yield db
    except RuntimeError as exc:
        raise AppError(
            code=ErrorCode.DATABASE_UNAVAILABLE,
            message="Database is not available. Please try again later.",
            http_status=status.HTTP_503_SERVICE_UNAVAILABLE,
        ) from exc
    except PyMongoError as exc:
        raise AppError(
            code=ErrorCode.DATABASE_UNAVAILABLE,
            message="Database is not available. Please try again later.",
            http_status=status.HTTP_503_SERVICE_UNAVAILABLE,
        ) from exc
