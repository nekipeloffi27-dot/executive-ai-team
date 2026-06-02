from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class BudgetCap(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    project_slug: str
    monthly_cap_cents: int = 15000
    hard_stop_pct: int = 80
    default_feature_cap_cents: int = 500
    default_thread_cap_cents: int = 100
    researcher_weekly_cap_cents: int = 1500
    curator_weekly_cap_cents: int = 1000
    updated_at: datetime
