"""Thread commands: /discuss, /threads, /decision."""
from __future__ import annotations
import json
from uuid import UUID
from aiogram import Router
from aiogram.filters import Command, CommandObject
from aiogram.types import Message
from core.config import settings
from core.db import get_pool
from core.enums import ThreadMode
from services.threads import create_thread, run_one_round, post_summary, ceo_decide, is_exhausted


def build_router(agent_registry) -> Router:
    r = Router(name="threads_cmd")

    @r.message(Command("discuss"))
    async def cmd_discuss(m: Message, command: CommandObject):
        """
        /discuss [deep] @designer @cto тема вопроса
        Создаёт thread, проводит max_rounds раундов, выдаёт summary.
        """
        if not command.args:
            await m.answer(
                "Использование:\n"
                "<code>/discuss [deep] @designer @cto тема вопроса</code>\n\n"
                "Доступные участники: @chief @designer @cto @researcher @strategist"
            )
            return
        tokens = command.args.split()
        mode = ThreadMode.DEFAULT
        idx = 0
        if tokens[0].lower() == "deep":
            mode = ThreadMode.DEEP
            idx = 1
        # participants — @mention'ы
        mention_map = {
            "@chief": "chief_of_staff", "@designer": "designer",
            "@cto": "cto_tasking", "@researcher": "researcher",
            "@strategist": "strategist",
        }
        participants = []
        while idx < len(tokens) and tokens[idx].startswith("@"):
            role = mention_map.get(tokens[idx].lower())
            if role:
                participants.append(role)
            idx += 1
        if not participants:
            participants = ["designer", "cto_tasking", "strategist"]
        question = " ".join(tokens[idx:]).strip()
        if not question:
            await m.answer("Нужна тема вопроса")
            return

        pool = get_pool()
        thread_id = await create_thread(
            pool, project_slug=settings.current_project_slug,
            topic=question[:200], initial_question=question,
            opened_by="ceo", participants=participants, mode=mode,
        )
        await m.answer(
            f"🧵 Thread открыт: <code>{thread_id}</code>\n"
            f"Mode: {mode.value} | Participants: {', '.join(participants)}\n"
            f"Запускаю раунды..."
        )

        # Подготовим agent runners для thread
        thread_runners = {}
        for role in participants:
            runner = agent_registry.get_oneshot_runner(role)
            if not runner:
                continue
            async def make_thread_runner(role_=role, runner_=runner):
                async def _r(pool_, tid, history):
                    history_text = "\n\n".join(
                        f"### {h['author']} (round {h['round_number']})\n{h['content']}"
                        for h in history
                    )
                    prompt = (
                        f"Ты участвуешь в обсуждении с командой. "
                        f"Прочти историю и добавь свою позицию. Кратко (1-2 параграфа), "
                        f"со ссылками на decisions/research если уместно. Если нечего добавить — отвечай '(pass)'.\n\n"
                        f"## История треда\n\n{history_text}"
                    )
                    result = await runner_(
                        pool_, prompt,
                        project_slug=settings.current_project_slug,
                        thread_id=tid, operation_kind="thread_round",
                    )
                    return result
                return _r
            thread_runners[role] = await make_thread_runner()

        # Прогоняем раунды
        while True:
            exhausted, reason = await is_exhausted(pool, thread_id)
            if exhausted:
                break
            res = await run_one_round(pool, thread_id, thread_runners)
            if "error" in res:
                break

        # Запрашиваем summary от Chief of Staff
        from agents.chief_of_staff.runner import summarize_thread_for_ceo
        summary_result = await post_summary(pool, thread_id, summarize_thread_for_ceo)
        await m.answer(
            f"📝 <b>Summary thread {str(thread_id)[:8]}</b>\n\n"
            f"{summary_result['content'][:3000]}\n\n"
            f"Используй <code>/decision {str(thread_id)[:8]} option_a</code> чтобы выбрать вариант."
        )

    @r.message(Command("threads"))
    async def cmd_threads(m: Message):
        pool = get_pool()
        async with pool.acquire() as c:
            rows = await c.fetch("""
                SELECT id, topic, status, mode, rounds_completed, messages_count
                FROM discussion_threads
                WHERE project_slug=$1 AND status IN ('open','awaiting_ceo')
                ORDER BY created_at DESC LIMIT 15
            """, settings.current_project_slug)
        if not rows:
            await m.answer("Активных threads нет")
            return
        lines = ["<b>Активные threads</b>"]
        for t in rows:
            lines.append(
                f"• <code>{str(t['id'])[:8]}</code> [{t['status']}/{t['mode']}] "
                f"r{t['rounds_completed']}/m{t['messages_count']} — {t['topic'][:60]}"
            )
        await m.answer("\n".join(lines))

    @r.message(Command("decision"))
    async def cmd_decision(m: Message, command: CommandObject):
        if not command.args:
            await m.answer("Использование: <code>/decision &lt;thread_id_prefix&gt; &lt;option_key или текст&gt;</code>")
            return
        parts = command.args.split(maxsplit=1)
        if len(parts) < 2:
            await m.answer("Нужны и thread_id и решение")
            return
        prefix = parts[0].strip()
        choice = parts[1].strip()
        pool = get_pool()
        async with pool.acquire() as c:
            row = await c.fetchrow("""
                SELECT id, topic FROM discussion_threads
                WHERE id::text LIKE $1 AND project_slug=$2 LIMIT 1
            """, prefix + "%", settings.current_project_slug)
        if not row:
            await m.answer("Thread не найден")
            return
        await ceo_decide(pool, row["id"], choice)
        # Сохраняем как decision
        async with pool.acquire() as c:
            await c.execute("""
                INSERT INTO decisions (project_slug, topic, decision, rationale, status)
                VALUES ($1, $2, $3, $4, 'active')
            """, settings.current_project_slug, row["topic"][:200], choice,
                 f"From thread {str(row['id'])[:8]}")
        await m.answer(f"✅ Решение зафиксировано для thread <code>{str(row['id'])[:8]}</code>: {choice[:200]}")

    return r
