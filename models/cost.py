from __future__ import annotations
from datetime import datetime
from decimal import Decimal
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class AgentCall(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    feature_id: UUID | None = None
    task_id: UUID | None = None
    thread_id: UUID | None = None
    agent_role: str
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    cache_creation_tokens: int = 0
    cache_read_tokens: int = 0
    cost_cents: Decimal = Decimal("0")
    duration_ms: int = 0
    iterations: int = 1
    success: bool = True
    error: str | None = None
    operation_kind: str | None = None
    created_at: datetime


class CostAttribution(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    project_slug: str
    agent_role: str
    feature_id: UUID | None = None
    task_id: UUID | None = None
    thread_id: UUID | None = None
    operation_kind: str
    model: str
    input_tokens: int
    output_tokens: int
    cost_cents: Decimal
    criticality: str
    created_at: datetime
