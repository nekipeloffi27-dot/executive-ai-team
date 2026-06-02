from __future__ import annotations
from core.config import settings
from agents.base import make_runner, AgentRegistry


def runner_factory(registry: AgentRegistry):
    return make_runner("researcher", settings.model_thinking, registry=registry)
