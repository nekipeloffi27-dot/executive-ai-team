"""Natural language fallback handler — routes free-text messages via NL Router."""
from __future__ import annotations
import time
import html as html_module
from aiogram import Router, F
from aiogram.types import Message, BufferedInputFile
from loguru import logger

from core.config import settings
from core.db import get_pool
from services.nl_router import route_message


def _looks_like_html_document(s: str) -> bool:
    """True если ответ содержит HTML-документ — лучше слать как файл."""
    lower = s[:500].lower()
    return ("<!doctype" in lower) or ("<html" in lower) or ("<head" in lower)


async def _send_agent_output(m: Message, target: str, content: str) -> None:
    """Безопасная отправка ответа агента: HTML-документ → как файл, иначе как сообщение."""
    if _looks_like_html_document(content):
        fname = f"{target}-{int(time.time())}.html"
        file = BufferedInputFile(content.encode("utf-8"), filename=fname)
        await m.answer_document(
            file,
            caption=f"📄 {target} вернул HTML-мокап ({len(content)} chars). Открой файл в браузере.",
        )
        return
    # обычный текст — но HTML-spec символы внутри code-блоков могут поломать парсер
    # на всякий случай если длинный — тоже файлом
    if len(content) > 4000:
        fname = f"{target}-{int(time.time())}.txt"
        file = BufferedInputFile(content.encode("utf-8"), filename=fname)
        await m.answer_document(file, caption=f"📄 {target} (длинный ответ, {len(content)} chars)")
        return
    try:
        await m.answer(content)
    except Exception:
        # parse_mode HTML мог не съесть — повторим с escape
        await m.answer(html_module.escape(content), parse_mode=None)


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
            await _send_agent_output(m, target, content)
        except Exception as e:
            logger.exception("NL fallback handler failed")
            await m.answer(f"⚠️ Ошибка: {e}")

    return r
