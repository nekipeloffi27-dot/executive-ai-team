"""Briefing: /briefing — Chief of Staff формирует ежедневную сводку."""
from __future__ import annotations
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from core.config import settings
from core.db import get_pool


def build_router(agent_registry) -> Router:
    r = Router(name="briefing_cmd")

    @r.message(Command("briefing"))
    async def cmd_briefing(m: Message):
        runner = agent_registry.get_oneshot_runner("chief_of_staff")
        if not runner:
            await m.answer("Chief of Staff не доступен")
            return
        pool = get_pool()
        prompt = (
            "Сформируй короткий daily briefing для CEO. Используй tools чтобы посмотреть:\n"
            "- активные threads и pending decisions\n"
            "- recent reflections (последние 2 дня)\n"
            "- бюджет — на каком проценте\n"
            "- что движется по фичам (если есть features в работе)\n\n"
            "Структура: 4-5 разделов, каждый 2-3 строки. Сначала Decisions Required, потом Movement, потом Risks, потом Budget."
        )
        await m.answer("📋 Готовлю briefing...")
        result = await runner(
            pool, prompt,
            project_slug=settings.current_project_slug,
            operation_kind="briefing",
        )
        content = (result.get("content") or "").strip()
        if not content:
            iters = result.get("iterations", "?")
            err = result.get("error") or "нет финального текста"
            content = f"⚠️ Chief не вернул briefing (итераций: {iters}). Причина: {err}"
        await m.answer(f"<b>📋 Daily Briefing</b>\n\n{content[:3500]}")

    return r
