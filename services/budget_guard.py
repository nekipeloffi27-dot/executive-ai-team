"""Budget-aware orchestration."""
from __future__ import annotations
import asyncpg
from loguru import logger
from core.enums import CRITICAL_AGENTS
from core.exceptions import BudgetExceeded


async def get_budget_status(pool: asyncpg.Pool, project_slug: str) -> dict:
    async with pool.acquire() as c:
        cap_row = await c.fetchrow(
            "SELECT * FROM budget_caps WHERE project_slug=$1", project_slug,
        )
        if not cap_row:
            return {"error": "No budget_caps for project"}
        # потрачено за текущий месяц
        spent_row = await c.fetchrow("""
            SELECT COALESCE(SUM(cost_cents), 0)::int AS spent_cents
            FROM cost_attributions
            WHERE project_slug=$1
              AND date_trunc('month', created_at) = date_trunc('month', NOW())
        """, project_slug)
        # breakdown по агентам
        by_agent = await c.fetch("""
            SELECT agent_role, COALESCE(SUM(cost_cents), 0)::int AS spent_cents
            FROM cost_attributions
            WHERE project_slug=$1
              AND date_trunc('month', created_at) = date_trunc('month', NOW())
            GROUP BY agent_role ORDER BY spent_cents DESC
        """, project_slug)

    cap = dict(cap_row)
    spent = int(spent_row["spent_cents"])
    pct = (spent / cap["monthly_cap_cents"]) * 100 if cap["monthly_cap_cents"] else 0
    return {
        "monthly_cap_cents": cap["monthly_cap_cents"],
        "spent_cents": spent,
        "pct_used": pct,
        "hard_stop_pct": cap["hard_stop_pct"],
        "remaining_cents": max(0, cap["monthly_cap_cents"] - spent),
        "by_agent": [dict(r) for r in by_agent],
    }


async def can_run(pool: asyncpg.Pool, project_slug: str, agent_role: str) -> tuple[bool, str]:
    """
    Возвращает (allowed, reason).
    Critical agents никогда не блокируются.
    Non-critical блокируются при достижении hard_stop_pct.
    """
    if agent_role in CRITICAL_AGENTS:
        return True, "critical_agent"
    status = await get_budget_status(pool, project_slug)
    if "error" in status:
        return True, "no_caps_configured"
    if status["pct_used"] >= status["hard_stop_pct"]:
        return False, (
            f"Budget hard-stop: {status['pct_used']:.1f}% used "
            f"(>= {status['hard_stop_pct']}% cap). Non-critical agents paused."
        )
    return True, "within_budget"


async def record_cost(
    pool: asyncpg.Pool, *,
    project_slug: str, agent_role: str,
    feature_id=None, task_id=None, thread_id=None,
    operation_kind: str, model: str,
    input_tokens: int, output_tokens: int, cost_cents: float,
) -> None:
    """Записывает атрибуцию в cost_attributions."""
    criticality = "critical" if agent_role in CRITICAL_AGENTS else "non_critical"
    try:
        async with pool.acquire() as c:
            await c.execute("""
                INSERT INTO cost_attributions
                    (project_slug, agent_role, feature_id, task_id, thread_id,
                     operation_kind, model, input_tokens, output_tokens, cost_cents, criticality)
                VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11)
            """, project_slug, agent_role, feature_id, task_id, thread_id,
                 operation_kind, model, input_tokens, output_tokens, cost_cents, criticality)
    except Exception as e:
        logger.warning("Failed to record cost attribution: {}", e)


def estimate_feature_cost_from_history(pool, project_slug: str) -> int:
    """TODO: для what-if сценариев. Реализуется в Phase 2."""
    return 450  # placeholder $4.50
