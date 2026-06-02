"""Lightweight tool: ask another agent a question, get one answer (no thread)."""
from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from agents.base import AgentRegistry


def tool_definitions() -> list[dict]:
    return [
        {
            "name": "ask_agent",
            "description": "Ask another team member a focused question. Returns their single answer (no back-and-forth). For real discussions use open_thread instead.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "agent_role": {"type": "string", "description": "designer|cto_tasking|cto_review|researcher|strategist|chief_of_staff"},
                    "question": {"type": "string"},
                },
                "required": ["agent_role", "question"],
            },
        },
    ]


async def execute(pool, project_slug: str, name: str, args: dict, registry: "AgentRegistry") -> str:
    if name != "ask_agent":
        return f"Unknown tool: {name}"
    target = args["agent_role"]
    runner = registry.get_oneshot_runner(target)
    if not runner:
        return f"Agent {target} not available"
    result = await runner(pool, args["question"], project_slug=project_slug, operation_kind="ask_agent")
    return result.get("content", "")[:5000]
