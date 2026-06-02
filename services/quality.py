from __future__ import annotations
import asyncpg
from core.enums import QualitySignalKind


async def log_signal(
    pool: asyncpg.Pool, *,
    kind: QualitySignalKind, target_agent_role: str, content: str,
    severity: str = "medium", source: str = "ceo",
    feature_id=None, task_id=None,
) -> int:
    async with pool.acquire() as c:
        row = await c.fetchrow("""
            INSERT INTO quality_signals
                (kind, target_agent_role, content, severity, source, feature_id, task_id)
            VALUES ($1,$2,$3,$4,$5,$6,$7) RETURNING id
        """, kind.value, target_agent_role, content, severity, source, feature_id, task_id)
    return row["id"]
