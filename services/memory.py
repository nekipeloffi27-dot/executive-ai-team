"""Unified memory layer for agents."""
from __future__ import annotations
import asyncpg
from typing import Any
from uuid import UUID


async def get_active_decisions(pool: asyncpg.Pool, project_slug: str) -> list[dict]:
    async with pool.acquire() as c:
        rows = await c.fetch("""
            SELECT id, topic, decision, rationale, created_at
            FROM decisions WHERE project_slug=$1 AND status='active'
            ORDER BY id ASC
        """, project_slug)
    return [dict(r) for r in rows]


async def add_decision(pool, project_slug: str, topic: str, decision: str, rationale: str = "") -> int:
    async with pool.acquire() as c:
        row = await c.fetchrow("""
            INSERT INTO decisions (project_slug, topic, decision, rationale, status)
            VALUES ($1, $2, $3, $4, 'active') RETURNING id
        """, project_slug, topic, decision, rationale)
    return row["id"]


async def get_roadmap(pool, project_slug: str, status: str | None = None) -> list[dict]:
    q = "SELECT * FROM roadmap_items WHERE project_slug=$1"
    args = [project_slug]
    if status:
        q += " AND status=$2"
        args.append(status)
    q += " ORDER BY priority DESC, created_at DESC"
    async with pool.acquire() as c:
        rows = await c.fetch(q, *args)
    return [dict(r) for r in rows]


async def get_recent_reflections(pool, agent_role: str | None = None, days: int = 7, limit: int = 50) -> list[dict]:
    q = """
        SELECT id, agent_role, task_description, went_well, uncertain_about,
               knowledge_gap, would_do_differently, outcome, created_at
        FROM agent_reflections
        WHERE created_at >= NOW() - ($1 || ' days')::interval
    """
    args: list[Any] = [str(days)]
    if agent_role:
        q += " AND agent_role=$2"
        args.append(agent_role)
    q += " ORDER BY created_at DESC LIMIT $%d" % (len(args) + 1)
    args.append(limit)
    async with pool.acquire() as c:
        rows = await c.fetch(q, *args)
    return [dict(r) for r in rows]


async def get_recent_quality_signals(pool, target_role: str | None = None, days: int = 14, limit: int = 100) -> list[dict]:
    q = """
        SELECT id, kind, target_agent_role, content, severity, source, created_at
        FROM quality_signals
        WHERE created_at >= NOW() - ($1 || ' days')::interval
    """
    args: list[Any] = [str(days)]
    if target_role:
        q += " AND target_agent_role=$2"
        args.append(target_role)
    q += " ORDER BY created_at DESC LIMIT $%d" % (len(args) + 1)
    args.append(limit)
    async with pool.acquire() as c:
        rows = await c.fetch(q, *args)
    return [dict(r) for r in rows]


async def get_recent_research_findings(pool, project_slug: str, days: int = 30, limit: int = 50) -> list[dict]:
    async with pool.acquire() as c:
        rows = await c.fetch("""
            SELECT id, source, topic, content, url, created_at
            FROM research_findings
            WHERE project_slug=$1 AND created_at >= NOW() - ($2 || ' days')::interval
            ORDER BY created_at DESC LIMIT $3
        """, project_slug, str(days), limit)
    return [dict(r) for r in rows]


async def get_thread(pool, thread_id: UUID) -> dict | None:
    async with pool.acquire() as c:
        row = await c.fetchrow("SELECT * FROM discussion_threads WHERE id=$1", thread_id)
    return dict(row) if row else None


async def get_thread_messages(pool, thread_id: UUID) -> list[dict]:
    async with pool.acquire() as c:
        rows = await c.fetch("""
            SELECT * FROM thread_messages WHERE thread_id=$1 ORDER BY id ASC
        """, thread_id)
    return [dict(r) for r in rows]


def format_decisions_for_prompt(decisions: list[dict]) -> str:
    if not decisions:
        return ""
    lines = ["## Active CEO Decisions\n"]
    for d in decisions[:15]:
        lines.append(f"- **{d['topic']}**: {d['decision']}")
        if d.get("rationale"):
            lines.append(f"  _Rationale: {d['rationale']}_")
    return "\n".join(lines)
