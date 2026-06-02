"""Multi-bot launcher. Starts 5 Telegram bots concurrently."""
from __future__ import annotations
import asyncio
from loguru import logger

from core.config import settings
from core.db import init_pool, close_pool
from core.logging_setup import setup_logging
from integrations.telegram_bot_registry import build_all_bots
from bot.middlewares.auth import WhitelistMiddleware
from bot.handlers import (
    admin as h_admin,
    nl as h_nl,
    feature_cmd as h_feature,
    context_cmd as h_context,
    budget_cmd as h_budget,
    threads_cmd as h_threads,
    research_cmd as h_research,
    skills_cmd as h_skills,
    briefing_cmd as h_briefing,
)
from agents.base import build_registry


async def main():
    setup_logging()
    pool = await init_pool()
    registry = build_registry()
    bots = build_all_bots()

    # Регистрируем handlers
    for name, entry in bots.items():
        # Whitelist на всех
        entry.dp.message.middleware(WhitelistMiddleware())
        # Admin commands — везде
        entry.dp.include_router(h_admin.build_router(name))

    # Chief bot — основной, держит все команды
    chief = bots["chief"]
    chief.dp.include_router(h_feature.build_router())
    chief.dp.include_router(h_context.build_router())
    chief.dp.include_router(h_budget.build_router())
    chief.dp.include_router(h_threads.build_router(registry))
    chief.dp.include_router(h_research.build_router(registry))
    chief.dp.include_router(h_skills.build_router())
    chief.dp.include_router(h_briefing.build_router(registry))
    chief.dp.include_router(h_nl.build_router(registry, bots))  # fallback последним

    # Остальные боты — только admin commands. NL fallback НЕ регистрируем
    # чтобы не дублировать ответ в группе (chief уже ловит свободный текст).
    # Не-chief боты постят от своего имени из логики handler'ов (threads, feature flow и т.д.).

    logger.info("Starting {} bots in parallel", len(bots))

    async def _run(entry):
        try:
            await entry.dp.start_polling(entry.bot, handle_signals=False)
        except Exception:
            logger.exception("Bot {} crashed", entry.name)

    try:
        await asyncio.gather(*(_run(e) for e in bots.values()))
    finally:
        for e in bots.values():
            await e.bot.session.close()
        await close_pool()


if __name__ == "__main__":
    asyncio.run(main())
