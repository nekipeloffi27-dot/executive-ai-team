"""Research command: /research <topic>."""
from __future__ import annotations
from aiogram import Router
from aiogram.filters import Command, CommandObject
from aiogram.types import Message
from core.config import settings
from core.db import get_pool


def build_router(agent_registry) -> Router:
    r = Router(name="research_cmd")

    @r.message(Command("research"))
    async def cmd_research(m: Message, command: CommandObject):
        if not command.args:
            await m.answer("Использование: <code>/research тема для ресерча</code>")
            return
        topic = command.args.strip()
        runner = agent_registry.get_oneshot_runner("researcher")
        if not runner:
            await m.answer("Researcher не доступен")
            return
        pool = get_pool()
        await m.answer(f"🔍 Researcher работает над: <i>{topic}</i>")
        result = await runner(
            pool, topic, project_slug=settings.current_project_slug,
            operation_kind="research_request",
        )
        if result.get("blocked"):
            await m.answer(f"⚠️ Заблокировано бюджетом: {result.get('reason')}")
            return
        content = result.get("content", "(пустой ответ)")
        # сохраняем как finding
        async with pool.acquire() as c:
            await c.execute("""
                INSERT INTO research_findings (project_slug, source, topic, content)
                VALUES ($1, 'researcher_agent', $2, $3)
            """, settings.current_project_slug, topic[:200], content[:8000])
        for chunk_start in range(0, min(len(content), 12000), 3500):
            await m.answer(content[chunk_start:chunk_start + 3500])

    return r
