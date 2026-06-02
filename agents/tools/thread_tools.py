"""Tools для работы с threads — открыть thread, ответить, прочитать историю."""
from __future__ import annotations
import asyncpg
import json
from uuid import UUID
from services.threads import create_thread, add_message
from services.memory import get_thread, get_thread_messages
from core.enums import ThreadMode


def tool_definitions() -> list[dict]:
    return [
        {
            "name": "open_thread",
            "description": "Open a new discussion thread with team members. Use when a decision needs cross-functional input (Designer + CTO + Strategist). Don't open for simple questions.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "topic": {"type": "string", "description": "Short topic (≤200 chars)"},
                    "initial_question": {"type": "string", "description": "Detailed question for participants"},
                    "participants": {
                        "type": "array", "items": {"type": "string"},
                        "description": "List of agent roles to invite (e.g. ['designer','cto_tasking','strategist'])",
                    },
                    "mode": {"type": "string", "enum": ["default", "deep"], "default": "default"},
                },
                "required": ["topic", "initial_question", "participants"],
            },
        },
        {
            "name": "read_thread",
            "description": "Read full history of a discussion thread.",
            "input_schema": {
                "type": "object",
                "properties": {"thread_id": {"type": "string"}},
                "required": ["thread_id"],
            },
        },
        {
            "name": "post_to_thread",
            "description": "Post a message to an existing open thread.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "thread_id": {"type": "string"},
                    "content": {"type": "string"},
                },
                "required": ["thread_id", "content"],
            },
        },
    ]


async def execute(
    pool: asyncpg.Pool, project_slug: str,
    name: str, args: dict, calling_agent: str,
) -> str:
    if name == "open_thread":
        thread_id = await create_thread(
            pool=pool, project_slug=project_slug,
            topic=args["topic"][:200],
            initial_question=args["initial_question"],
            opened_by=calling_agent,
            participants=args["participants"],
            mode=ThreadMode.DEEP if args.get("mode") == "deep" else ThreadMode.DEFAULT,
        )
        return f"Thread opened: {thread_id}"

    if name == "read_thread":
        t = await get_thread(pool, UUID(args["thread_id"]))
        if not t:
            return "Thread not found"
        msgs = await get_thread_messages(pool, UUID(args["thread_id"]))
        return json.dumps({
            "thread": {k: str(v) for k, v in t.items()},
            "messages": [{"author": m["author"], "content": m["content"], "round": m["round_number"]} for m in msgs],
        }, default=str, ensure_ascii=False)

    if name == "post_to_thread":
        await add_message(
            pool, thread_id=UUID(args["thread_id"]),
            author=calling_agent, content=args["content"],
        )
        return "Message posted"

    return f"Unknown thread tool: {name}"
