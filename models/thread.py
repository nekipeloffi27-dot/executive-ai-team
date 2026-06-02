from __future__ import annotations
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict
from core.enums import ThreadStatus, ThreadMode


class ThreadMessage(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    thread_id: UUID
    author: str
    content: str
    citations: list[dict] = []
    is_summary: bool = False
    round_number: int = 1
    created_at: datetime


class DiscussionThread(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    project_slug: str
    topic: str
    initial_question: str
    opened_by: str
    participants: list[str] = []
    status: ThreadStatus
    mode: ThreadMode = ThreadMode.DEFAULT
    max_rounds: int = 3
    max_messages: int = 8
    budget_cap_cents: int = 100
    budget_used_cents: int = 0
    rounds_completed: int = 0
    messages_count: int = 0
    tg_thread_id: int | None = None
    related_feature_id: UUID | None = None
    ceo_options: dict | None = None
    ceo_decision: str | None = None
    created_at: datetime
    decided_at: datetime | None = None
