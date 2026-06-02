"""Feature commands: /feature, /status, /cancel, /unblock, /retry."""
from __future__ import annotations
import asyncpg
from uuid import UUID
from aiogram import Router
from aiogram.filters import Command, CommandObject
from aiogram.types import Message
from loguru import logger

from core.config import settings
from core.db import get_pool


def build_router() -> Router:
    r = Router(name="feature_cmd")

    @r.message(Command("feature"))
    async def cmd_feature(m: Message, command: CommandObject):
        """Создать новую фичу."""
        text = command.args
        if not text:
            await m.answer("Использование: <code>/feature описание фичи</code>")
            return
        pool = get_pool()
        async with pool.acquire() as c:
            row = await c.fetchrow("""
                INSERT INTO features (project_slug, title, description, state, mode)
                VALUES ($1, $2, $3, 'clarification', 'new')
                RETURNING id
            """, settings.current_project_slug, text[:200], text)
        await m.answer(
            f"✅ Фича создана: <code>{row['id']}</code>\n"
            f"State: <code>clarification</code>\n"
            f"Chief of Staff подхватит и начнёт уточнение."
        )

    @r.message(Command("status"))
    async def cmd_status(m: Message, command: CommandObject):
        """Показать статус фичи или всех фич в работе."""
        pool = get_pool()
        if command.args:
            try:
                fid = UUID(command.args.strip())
            except Exception:
                await m.answer("Некорректный feature_id")
                return
            async with pool.acquire() as c:
                row = await c.fetchrow("SELECT * FROM features WHERE id=$1", fid)
            if not row:
                await m.answer("Не найдено")
                return
            await m.answer(
                f"<b>{row['title']}</b>\n"
                f"State: <code>{row['state']}</code>\n"
                f"Budget: ${row['budget_used_cents']/100:.2f} / ${row['budget_cap_cents']/100:.2f}\n"
                f"Created: {row['created_at']}\n"
                f"Updated: {row['updated_at']}"
            )
            return
        async with pool.acquire() as c:
            rows = await c.fetch("""
                SELECT id, title, state FROM features
                WHERE project_slug=$1 AND state NOT IN ('cancelled','prod_deployed','failed')
                ORDER BY updated_at DESC LIMIT 20
            """, settings.current_project_slug)
        if not rows:
            await m.answer("Активных фич нет")
            return
        lines = ["<b>Активные фичи</b>"]
        for r_ in rows:
            lines.append(f"• <code>{str(r_['id'])[:8]}</code> [{r_['state']}] {r_['title'][:60]}")
        await m.answer("\n".join(lines))

    @r.message(Command("cancel"))
    async def cmd_cancel(m: Message, command: CommandObject):
        if not command.args:
            await m.answer("Использование: <code>/cancel &lt;feature_id&gt;</code>")
            return
        try:
            fid = UUID(command.args.strip())
        except Exception:
            await m.answer("Некорректный feature_id")
            return
        pool = get_pool()
        async with pool.acquire() as c:
            await c.execute("""
                UPDATE features SET state='cancelled', cancelled_at=NOW(), updated_at=NOW()
                WHERE id=$1
            """, fid)
        # Также убиваем sandbox если запущен
        from agents.dev.runner import cancel_sandbox
        async with pool.acquire() as c:
            tasks = await c.fetch("SELECT id FROM tasks WHERE feature_id=$1 AND status='in_progress'", fid)
        for t in tasks:
            try:
                await cancel_sandbox(t["id"])
            except Exception as e:
                logger.warning("Failed to cancel sandbox for task {}: {}", t["id"], e)
        await m.answer(f"❌ Фича {str(fid)[:8]} отменена")

    @r.message(Command("unblock"))
    async def cmd_unblock(m: Message, command: CommandObject):
        """Снять blocked-state с фичи (если завис state machine)."""
        if not command.args:
            await m.answer("Использование: <code>/unblock &lt;feature_id&gt; [новое состояние]</code>")
            return
        parts = command.args.split(maxsplit=1)
        try:
            fid = UUID(parts[0].strip())
        except Exception:
            await m.answer("Некорректный feature_id")
            return
        new_state = parts[1].strip() if len(parts) > 1 else "clarification"
        pool = get_pool()
        async with pool.acquire() as c:
            await c.execute("""
                UPDATE features SET state=$2, updated_at=NOW() WHERE id=$1 AND state='blocked'
            """, fid, new_state)
            await c.execute("""
                INSERT INTO state_transitions (feature_id, from_state, to_state, triggered_by, reason)
                VALUES ($1, 'blocked', $2, 'ceo', 'manual unblock')
            """, fid, new_state)
        await m.answer(f"✅ Фича {str(fid)[:8]} разблокирована → <code>{new_state}</code>")

    @r.message(Command("retry"))
    async def cmd_retry(m: Message, command: CommandObject):
        """Перезапустить последнюю упавшую таску в фиче."""
        if not command.args:
            await m.answer("Использование: <code>/retry &lt;feature_id&gt;</code>")
            return
        try:
            fid = UUID(command.args.strip())
        except Exception:
            await m.answer("Некорректный feature_id")
            return
        pool = get_pool()
        async with pool.acquire() as c:
            row = await c.fetchrow("""
                SELECT id, title FROM tasks
                WHERE feature_id=$1 AND status='failed'
                ORDER BY updated_at DESC LIMIT 1
            """, fid)
        if not row:
            await m.answer("Нет упавших тасок для перезапуска")
            return
        async with pool.acquire() as c:
            await c.execute("UPDATE tasks SET status='pending', updated_at=NOW() WHERE id=$1", row["id"])
        await m.answer(
            f"♻️ Таска <code>{str(row['id'])[:8]}</code> ({row['title']}) → pending. "
            f"Оркестратор подхватит её следующим тиком."
        )

    return r
