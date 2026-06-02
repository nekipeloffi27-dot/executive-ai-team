from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from core.enums import DecisionStatus


class Decision(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    project_slug: str
    topic: str
    decision: str
    rationale: str | None = None
    status: DecisionStatus = DecisionStatus.ACTIVE
    supersedes: int | None = None
    created_at: datetime


class CEOPendingDecision(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    project_slug: str
    title: str
    description: str
    urgency: str = "normal"
    related_thread_id: str | None = None  # UUID as str for flexibility
    related_feature_id: str | None = None
    choices: list[dict] = []
    proposed_by: str
    decided: bool = False
    ceo_choice: str | None = None
    created_at: datetime
    decided_at: datetime | None = None
