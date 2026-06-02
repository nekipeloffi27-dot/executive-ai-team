"""Budget commands: /budget, /cost."""
from __future__ import annotations
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from core.config import settings
from core.db import get_pool
from services.budget_guard import get_budget_status


def build_router() -> Router:
    r = Router(name="budget_cmd")

    @r.message(Command("budget"))
    async def cmd_budget(m: Message):
        pool = get_pool()
        status = await get_budget_status(pool, settings.current_project_slug)
        if "error" in status:
            await m.answer(f"⚠️ {status['error']}")
            return
        lines = [
            "<b>Месячный бюджет</b>",
            f"Cap: ${status['monthly_cap_cents']/100:.2f}",
            f"Spent: ${status['spent_cents']/100:.2f} ({status['pct_used']:.1f}%)",
            f"Remaining: ${status['remaining_cents']/100:.2f}",
            f"Hard-stop at: {status['hard_stop_pct']}%",
            "",
            "<b>By agent</b>",
        ]
        for a in status["by_agent"][:10]:
            lines.append(f"  {a['agent_role']}: ${a['spent_cents']/100:.2f}")
        await m.answer("\n".join(lines))

    @r.message(Command("cost"))
    async def cmd_cost(m: Message):
        pool = get_pool()
        async with pool.acquire() as c:
            today = await c.fetchrow("""
                SELECT COALESCE(SUM(cost_cents), 0)::int AS s
                FROM cost_attributions
                WHERE project_slug=$1 AND created_at >= NOW() - interval '1 day'
            """, settings.current_project_slug)
            week = await c.fetchrow("""
                SELECT COALESCE(SUM(cost_cents), 0)::int AS s
                FROM cost_attributions
                WHERE project_slug=$1 AND created_at >= NOW() - interval '7 days'
            """, settings.current_project_slug)
        await m.answer(
            f"<b>Cost</b>\n"
            f"Last 24h: ${today['s']/100:.2f}\n"
            f"Last 7d: ${week['s']/100:.2f}"
        )

    return r
