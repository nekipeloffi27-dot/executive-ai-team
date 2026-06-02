"""Tools для чтения памяти агентами."""
from __future__ import annotations
import asyncpg
import json
from services.memory import (
    get_active_decisions, get_recent_reflections,
    get_recent_quality_signals, get_recent_research_findings, get_roadmap,
)


def tool_definitions() -> list[dict]:
    """Tools которые агенты могут вызывать для чтения памяти."""
    return [
        {
            "name": "read_decisions",
            "description": "Read all active CEO decisions for the project. Use when you need to align with what's been decided.",
            "input_schema": {"type": "object", "properties": {}, "required": []},
        },
        {
            "name": "read_roadmap",
            "description": "Read project roadmap items. Optional status filter: proposed/accepted/in_progress/done/dropped.",
            "input_schema": {
                "type": "object",
                "properties": {"status": {"type": "string"}},
                "required": [],
            },
        },
        {
            "name": "read_recent_reflections",
            "description": "Read recent self-reflections from team agents. Useful for understanding where the team has been struggling.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "agent_role": {"type": "string", "description": "Filter by role (optional)"},
                    "days": {"type": "integer", "default": 7},
                },
                "required": [],
            },
        },
        {
            "name": "read_research_findings",
            "description": "Read recent research findings (competitor analysis, market trends) for the project.",
            "input_schema": {
                "type": "object",
                "properties": {"days": {"type": "integer", "default": 30}},
                "required": [],
            },
        },
        {
            "name": "read_quality_signals",
            "description": "Read recent quality signals (CEO feedback, redo_design, request_changes etc).",
            "input_schema": {
                "type": "object",
                "properties": {
                    "target_role": {"type": "string"},
                    "days": {"type": "integer", "default": 14},
                },
                "required": [],
            },
        },
    ]


async def execute(pool: asyncpg.Pool, project_slug: str, name: str, args: dict) -> str:
    if name == "read_decisions":
        rows = await get_active_decisions(pool, project_slug)
        return json.dumps(rows, default=str, ensure_ascii=False)
    if name == "read_roadmap":
        rows = await get_roadmap(pool, project_slug, status=args.get("status"))
        return json.dumps(rows, default=str, ensure_ascii=False)
    if name == "read_recent_reflections":
        rows = await get_recent_reflections(
            pool, agent_role=args.get("agent_role"), days=args.get("days", 7),
        )
        return json.dumps(rows, default=str, ensure_ascii=False)
    if name == "read_research_findings":
        rows = await get_recent_research_findings(pool, project_slug, days=args.get("days", 30))
        return json.dumps(rows, default=str, ensure_ascii=False)
    if name == "read_quality_signals":
        rows = await get_recent_quality_signals(
            pool, target_role=args.get("target_role"), days=args.get("days", 14),
        )
        return json.dumps(rows, default=str, ensure_ascii=False)
    return f"Unknown memory tool: {name}"
