"""Skills commands: /skills pending|run, /skill_approve|reject|disable."""
from __future__ import annotations
from pathlib import Path
from aiogram import Router
from aiogram.filters import Command, CommandObject
from aiogram.types import Message
from core.config import settings
from core.db import get_pool
from services.skill_curator import run_curator


def build_router() -> Router:
    r = Router(name="skills_cmd")

    @r.message(Command("skills"))
    async def cmd_skills(m: Message, command: CommandObject):
        sub = (command.args or "pending").strip().lower()
        pool = get_pool()
        if sub == "pending":
            async with pool.acquire() as c:
                rows = await c.fetch("""
                    SELECT id, name, target_agent_role, rationale, estimated_cost_impact_cents, created_at
                    FROM skill_proposals
                    WHERE status='proposed'
                    ORDER BY created_at DESC LIMIT 20
                """)
            if not rows:
                await m.answer("Нет pending skill proposals")
                return
            lines = ["<b>Skill proposals (pending)</b>"]
            for s in rows:
                lines.append(
                    f"\n#<code>{s['id']}</code> for <b>{s['target_agent_role']}</b>: "
                    f"<i>{s['name']}</i>\n"
                    f"  Impact: ${(s['estimated_cost_impact_cents'] or 0)/100:+.2f}/feature\n"
                    f"  {s['rationale'][:300]}"
                )
            await m.answer("\n".join(lines)[:4000])
            return
        if sub == "run":
            await m.answer("🧠 Запускаю Skill Curator...")
            n = await run_curator(pool, settings.current_project_slug)
            await m.answer(f"Готово. Создано предложений: {n}")
            return
        await m.answer("Подкоманды: /skills pending | run")

    @r.message(Command("skill_approve"))
    async def cmd_approve(m: Message, command: CommandObject):
        if not command.args:
            await m.answer("Использование: <code>/skill_approve &lt;id&gt;</code>")
            return
        try:
            sid = int(command.args.strip())
        except Exception:
            await m.answer("ID должен быть числом")
            return
        pool = get_pool()
        async with pool.acquire() as c:
            row = await c.fetchrow("SELECT * FROM skill_proposals WHERE id=$1", sid)
            if not row:
                await m.answer("Не найдено")
                return
            # пишем SKILL.md
            target_dir = Path(settings.skills_dir) / row["target_agent_role"] / row["name"]
            target_dir.mkdir(parents=True, exist_ok=True)
            (target_dir / "SKILL.md").write_text(row["draft_content"], encoding="utf-8")
            await c.execute(
                "UPDATE skill_proposals SET status='approved', decided_at=NOW() WHERE id=$1", sid
            )
        await m.answer(
            f"✅ Skill <code>{row['name']}</code> approved → монтируется к {row['target_agent_role']}.\n"
            f"Файл: <code>{settings.skills_dir}/{row['target_agent_role']}/{row['name']}/SKILL.md</code>"
        )

    @r.message(Command("skill_reject"))
    async def cmd_reject(m: Message, command: CommandObject):
        if not command.args:
            await m.answer("Использование: <code>/skill_reject &lt;id&gt;</code>")
            return
        try:
            sid = int(command.args.strip())
        except Exception:
            await m.answer("ID должен быть числом")
            return
        pool = get_pool()
        async with pool.acquire() as c:
            await c.execute(
                "UPDATE skill_proposals SET status='rejected', decided_at=NOW() WHERE id=$1", sid
            )
        await m.answer(f"❌ Skill #{sid} rejected")

    @r.message(Command("skill_disable"))
    async def cmd_disable(m: Message, command: CommandObject):
        if not command.args:
            await m.answer("Использование: <code>/skill_disable &lt;name&gt;</code>")
            return
        name = command.args.strip()
        pool = get_pool()
        async with pool.acquire() as c:
            await c.execute(
                "UPDATE skill_proposals SET status='disabled' WHERE name=$1 AND status='approved'", name
            )
        # Удаляем файл
        for role_dir in Path(settings.skills_dir).iterdir():
            target = role_dir / name / "SKILL.md"
            if target.exists():
                target.unlink()
                await m.answer(f"⏸ Skill <code>{name}</code> disabled (file removed)")
                return
        await m.answer(f"Skill <code>{name}</code> не найден")

    return r
