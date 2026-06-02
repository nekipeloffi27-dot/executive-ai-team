from __future__ import annotations
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict
from core.enums import FeatureState


class Feature(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    project_slug: str
    title: str
    description: str
    state: FeatureState
    mode: str = "new"
    context: dict = {}
    budget_cap_cents: int = 500
    budget_used_cents: int = 0
    tg_thread_id: int | None = None
    created_at: datetime
    updated_at: datetime
    cancelled_at: datetime | None = None
    deployed_at: datetime | None = None
