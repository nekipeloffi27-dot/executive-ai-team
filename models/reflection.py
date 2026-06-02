from __future__ import annotations
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class AgentReflection(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    agent_role: str
    feature_id: UUID | None = None
    task_id: UUID | None = None
    thread_id: UUID | None = None
    task_description: str
    went_well: str | None = None
    uncertain_about: str | None = None
    knowledge_gap: str | None = None
    would_do_differently: str | None = None
    outcome: str = "completed"
    created_at: datetime
