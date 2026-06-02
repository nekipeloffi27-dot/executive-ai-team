from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class ResearchFinding(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    project_slug: str
    source: str
    topic: str
    content: str
    relevance_tags: list[str] = []
    url: str | None = None
    created_at: datetime
