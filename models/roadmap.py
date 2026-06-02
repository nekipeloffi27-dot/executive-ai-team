from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class RoadmapItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    project_slug: str
    title: str
    description: str | None = None
    phase: str | None = None
    priority: int = 100
    status: str = "proposed"
    proposed_by: str | None = None
    estimated_cost_cents: int | None = None
    created_at: datetime
    decided_at: datetime | None = None
