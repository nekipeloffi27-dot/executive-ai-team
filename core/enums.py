"""Enumerations used across the system."""
from __future__ import annotations
from enum import Enum


class FeatureState(str, Enum):
    """State machine for feature delivery."""
    CLARIFICATION = "clarification"     # PM/Chief уточняет
    DESIGN_PENDING = "design_pending"
    DESIGN_REVIEW = "design_review"
    TASKS_PENDING = "tasks_pending"     # CTO нарезает
    CODING = "coding"
    REVIEW = "review"                   # CTO review PR'ов
    DEV_DEPLOYED = "dev_deployed"
    TESTING = "testing"
    PROD_READY = "prod_ready"
    PROD_DEPLOYED = "prod_deployed"
    BLOCKED = "blocked"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskType(str, Enum):
    BACKEND = "backend"
    FRONTEND_WEB = "frontend_web"
    FRONTEND_MOBILE = "frontend_mobile"


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    PR_OPEN = "pr_open"
    APPROVED = "approved"
    REQUEST_CHANGES = "request_changes"
    MERGED = "merged"
    FAILED = "failed"


class TaskComplexity(str, Enum):
    SIMPLE = "simple"
    MEDIUM = "medium"
    COMPLEX = "complex"


class AgentRole(str, Enum):
    CHIEF_OF_STAFF = "chief_of_staff"
    RESEARCHER = "researcher"
    STRATEGIST = "strategist"
    DESIGNER = "designer"
    CTO_TASKING = "cto_tasking"
    CTO_REVIEW = "cto_review"
    DEV_BACKEND = "dev_backend"
    DEV_FRONTEND_WEB = "dev_frontend_web"
    DEV_FRONTEND_MOBILE = "dev_frontend_mobile"
    SKILL_CURATOR = "skill_curator"
    NL_ROUTER = "nl_router"


class ThreadStatus(str, Enum):
    OPEN = "open"
    AWAITING_CEO = "awaiting_ceo"
    DECIDED = "decided"
    ARCHIVED = "archived"
    EXHAUSTED = "exhausted"  # достиг cap'а


class ThreadMode(str, Enum):
    DEFAULT = "default"      # 3 раунда / 8 сообщений / $1
    DEEP = "deep"            # 5 / 15 / $3


class DecisionStatus(str, Enum):
    ACTIVE = "active"
    SUPERSEDED = "superseded"
    REVERTED = "reverted"


class SkillProposalStatus(str, Enum):
    PROPOSED = "proposed"
    APPROVED = "approved"
    REJECTED = "rejected"
    DISABLED = "disabled"


class QualitySignalKind(str, Enum):
    REDO_DESIGN = "redo_design"
    FAIL_TEST = "fail_test"
    CTO_REQUEST_CHANGES = "cto_request_changes"
    CEO_FEEDBACK = "ceo_feedback"
    BUDGET_OVERRUN = "budget_overrun"


CRITICAL_AGENTS = {
    AgentRole.DESIGNER.value,
    AgentRole.CTO_TASKING.value,
    AgentRole.CTO_REVIEW.value,
    AgentRole.DEV_BACKEND.value,
    AgentRole.DEV_FRONTEND_WEB.value,
    AgentRole.DEV_FRONTEND_MOBILE.value,
}
