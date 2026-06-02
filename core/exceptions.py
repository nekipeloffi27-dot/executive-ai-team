"""Custom exceptions."""
from __future__ import annotations


class ExecutiveTeamError(Exception):
    """Base exception."""


class BudgetExceeded(ExecutiveTeamError):
    """Raised when a budget cap is hit."""


class ThreadCapReached(ExecutiveTeamError):
    """Raised when thread hits max rounds/messages."""


class AgenticIterationLimitReached(ExecutiveTeamError):
    """Raised when agent loop hits max iterations without final answer."""


class SandboxError(ExecutiveTeamError):
    """Raised when sandbox container fails to start, run, or finish."""


class ContextNotFound(ExecutiveTeamError):
    """Raised when required project context file is missing."""


class InvalidStateTransition(ExecutiveTeamError):
    """Raised on invalid feature state transition."""
