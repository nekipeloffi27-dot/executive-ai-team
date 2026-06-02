from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from core.enums import SkillProposalStatus


class SkillProposal(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    target_agent_role: str
    rationale: str
    draft_content: str
    estimated_cost_impact_cents: int | None = None
    evidence_reflection_ids: list[int] = []
    evidence_signal_ids: list[int] = []
    status: SkillProposalStatus = SkillProposalStatus.PROPOSED
    decided_at: datetime | None = None
    created_at: datetime
