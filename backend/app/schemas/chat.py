"""
Sorim.AI — Chat Schemas  (schemas/chat.py)

Pydantic schemas matching API_CONTRACTS.md §1.9, §6 and DATA_MODEL.md §3.4.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.analysis import ChatRecord


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    employee_id: str = Field(min_length=1, max_length=32)
    message: str = Field(min_length=1, max_length=2000)
    conversation_id: str | None = None
