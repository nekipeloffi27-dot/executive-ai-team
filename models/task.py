from __future__ import annotations
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict
from core.enums import TaskType, TaskStatus, TaskComplexity


class Task(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    feature_id: UUID
    type: TaskType
    status: TaskStatus
    complexity: TaskComplexity
    title: str
    description: str
    affected_files: list[str] = []
    changes_per_file: list[dict] = []
    acceptance_criteria: list[str] = []
    api_contract: dict | None = None
    pr_url: str | None = None
    pr_number: int | None = None
    branch_name: str | None = None
    cto_review_verdict: str | None = None
    cto_review_comments: str | None = None
    created_at: datetime
    updated_at: datetime
