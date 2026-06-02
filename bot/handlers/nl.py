"""Natural language fallback handler — routes free-text messages via NL Router."""
from __future__ import annotations
from aiogram import Router, F
from aiogram.types import Message
from loguru import logger

from core.config import settings
from core.db import get_pool
from services.nl_router import route_message


def build_router(agent_registry, bots) -> Router:
    r = Router(name="nl_fallback")

    @r.message(F.text & ~F.text.startswith("/"))
    async def handle_text(m: Message):
        if not settings.nl_router_enabled:
            return
        pool = get_pool()
        routed = await route_message(pool, m.text or "")
        intent = routed.get("intent", "unknown")
        target = routed.get("target_agent", "chief_of_staff")
        summary = routed.get("summary", "")

        if intent == "chitchat":
            await m.answer("(Chief): hi! Чем помочь?")
            return

        if intent == "unknown":
            await m.answer(
                "Не понял намерения. Используй команды:\n"
                "/feature, /research, /discuss, /context, /budget, /briefing, /skills"
            )
            return

        # Маршрутизируем к целевому агенту
        runner = agent_registry.get_oneshot_runner(target)
        if not runner:
            await m.answer(f"Агент <code>{target}</code> недоступен")
            return

        thinking_msg = await m.answer(f"🤔 {target} думает...")
        try:
            result = await runner(
                pool, summary or m.text,
                project_slug=settings.current_project_slug,
            )
            content = (result.get("content") or "").strip()
            if result.get("blocked"):
                content = f"⚠️ Заблокировано бюджет-стражем: {result.get('reason')}"
            if not content:
                iters = result.get("iterations", "?")
                err = result.get("error") or "нет финального текста"
                content = (
                    f"⚠️ {target} не дал ответа (итераций: {iters}). "
                    f"Причина: {err}. Попробуй переформулировать или прямую команду."
                )
            await thinking_msg.delete()
            # отправка от соответствующего бота — упрощено: отвечаем тем же ботом
            await m.answer(content[:4000])
        except Exception as e:
            logger.exception("NL fallback handler failed")
            await m.answer(f"⚠️ Ошибка: {e}")

    return r
