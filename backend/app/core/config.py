"""
Sorim.AI — Application Configuration

Reads settings from environment variables only.
Secrets are never logged.
Supports both MONGODB_DB_NAME and MONGODB_DATABASE (OQ-24).
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _resolve_env_file() -> str:
    """Find the project-local .env regardless of whether the app runs from repo root or backend/."""
    repo_root = Path(__file__).resolve().parents[2]
    candidates = [
        repo_root / "backend" / ".env",
        repo_root / ".env",
        Path.cwd() / ".env",
        Path.cwd() / "backend" / ".env",
    ]
    for path in candidates:
        if path.exists():
            return str(path)
    return str(repo_root / "backend" / ".env")


class Settings(BaseSettings):
    """All application settings sourced from environment variables."""

    model_config = SettingsConfigDict(
        env_file=_resolve_env_file(),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    def __init__(self, **values):
        """Prefer the explicitly provided Mongo DB name when one alias is supplied."""
        if "mongodb_db_name" in values and "mongodb_database" not in values:
            values["mongodb_database"] = values["mongodb_db_name"]
        elif "mongodb_database" in values and "mongodb_db_name" not in values:
            values["mongodb_db_name"] = values["mongodb_database"]

        if "hf_llm_model_id" in values and "llm_model_id" not in values:
            values["llm_model_id"] = values["hf_llm_model_id"]
        elif "llm_model_id" in values and "hf_llm_model_id" not in values:
            values["hf_llm_model_id"] = values["llm_model_id"]

        super().__init__(**values)

    # ── Application ──────────────────────────────────────────────────────────
    app_env: str = "development"
    app_version: str = "0.1.0"
    log_level: str = "INFO"

    # ── CORS ─────────────────────────────────────────────────────────────────
    cors_allowed_origins: str = "http://localhost:5173"

    # ── MongoDB ───────────────────────────────────────────────────────────────
    # URI is required; absence raises a clear error at startup.
    mongodb_uri: Optional[str] = None

    # Support both documented variable names (OQ-24 dual-support).
    # The application uses `db_name` internally.
    mongodb_db_name: Optional[str] = None
    mongodb_database: Optional[str] = None
    mongodb_timeout_ms: int = 10000

    # ── ServiceNow ───────────────────────────────────────────────────────────
    servicenow_mode: str = "mock"

    # ── AI / RAG ──────────────────────────────────────────────────────────────
    confidence_threshold: float = 0.60
    llm_model_id: str = "Qwen/Qwen2.5-1.5B-Instruct"
    hf_llm_model_id: Optional[str] = None
    llm_device: str = "cpu"
    llm_max_new_tokens_analysis: int = 256
    embedding_model_id: str = "sentence-transformers/all-MiniLM-L6-v2"
    chroma_persist_dir: str = "./.chroma"
    knowledge_base_dir: str = "../knowledge_base"
    retrieval_top_k: int = 4
    llm_allow_download: bool = False

    @model_validator(mode="after")
    def resolve_db_name(self) -> "Settings":
        """Resolve the canonical database name from the two supported env vars."""
        name_a = self.mongodb_db_name
        name_b = self.mongodb_database
        explicit_names = set(self.model_fields_set) & {"mongodb_db_name", "mongodb_database"}

        if "mongodb_db_name" in explicit_names and "mongodb_database" not in explicit_names:
            resolved = name_a or "itsm_helpdesk"
        elif "mongodb_database" in explicit_names and "mongodb_db_name" not in explicit_names:
            resolved = name_b or "itsm_helpdesk"
        else:
            if name_a and name_b and name_a != name_b:
                raise ValueError(
                    f"MONGODB_DB_NAME ('{name_a}') and MONGODB_DATABASE ('{name_b}') "
                    "are both set but disagree. Set them to the same value or remove one."
                )
            resolved = name_a or name_b or "itsm_helpdesk"

        object.__setattr__(self, "db_name", resolved)
        return self

    @model_validator(mode="after")
    def resolve_model_id(self) -> "Settings":
        """Resolve canonical LLM model ID from LLM_MODEL_ID and HF_LLM_MODEL_ID."""
        model_a = self.llm_model_id
        model_b = self.hf_llm_model_id
        explicit_models = set(self.model_fields_set) & {"llm_model_id", "hf_llm_model_id"}

        if "hf_llm_model_id" in explicit_models and "llm_model_id" not in explicit_models:
            resolved = model_b or "Qwen/Qwen2.5-1.5B-Instruct"
        elif "llm_model_id" in explicit_models and "hf_llm_model_id" not in explicit_models:
            resolved = model_a or "Qwen/Qwen2.5-1.5B-Instruct"
        else:
            if model_a and model_b and model_a != model_b:
                raise ValueError(
                    f"LLM_MODEL_ID ('{model_a}') and HF_LLM_MODEL_ID ('{model_b}') "
                    "are both set but disagree. Set them to the same value or remove one."
                )
            resolved = model_a or model_b or "Qwen/Qwen2.5-1.5B-Instruct"

        resolved = (resolved or "").strip()
        if not resolved:
            raise ValueError("Configured LLM model ID cannot be empty.")
        object.__setattr__(self, "llm_model_id", resolved)
        return self

    @field_validator("servicenow_mode")
    @classmethod
    def validate_servicenow_mode(cls, v: str) -> str:
        allowed = {"mock"}  # "live" is rejected — no live adapter in v1 (ARCHITECTURE §3.1)
        if v not in allowed:
            raise ValueError(
                f"SERVICENOW_MODE='{v}' is not supported. "
                "Only 'mock' is available in v1. A live adapter is documented only."
            )
        return v

    @property
    def is_development(self) -> bool:
        return self.app_env.lower() == "development"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_allowed_origins.split(",") if o.strip()]

    def safe_db_info(self) -> dict:
        """Return loggable DB info — never reveals the URI or credentials."""
        db_name = getattr(self, "db_name", "itsm_helpdesk")
        # Extract only the host portion from the URI without credentials.
        uri = self.mongodb_uri or ""
        host_hint = "not configured"
        if uri:
            # Strip credentials: mongodb+srv://user:pass@host/... → host
            try:
                at_idx = uri.rfind("@")
                slash_idx = uri.find("/", at_idx if at_idx != -1 else 0)
                if at_idx != -1:
                    host_part = uri[at_idx + 1:]
                    q_idx = host_part.find("?")
                    host_hint = host_part[:q_idx] if q_idx != -1 else host_part
                else:
                    host_hint = "configured (scheme without credentials)"
            except Exception:
                host_hint = "configured"
        return {"host_hint": host_hint, "db_name": db_name, "timeout_ms": self.mongodb_timeout_ms}


# Module-level singleton — imported everywhere via get_settings().
@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the cached Settings singleton.

    Raises ValueError on misconfiguration. Called at startup so errors
    surface before the application accepts requests.
    """
    return Settings()
