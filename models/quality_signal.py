from __future__ import annotations
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict
from core.enums import QualitySignalKind


class QualitySignal(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    kind: QualitySignalKind
    target_agent_role: str
    content: str
    severity: str = "medium"
    source: str
    feature_id: UUID | None = None
    task_id: UUID | None = None
    created_at: datetime
