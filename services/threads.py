"""Thread Engine — discussions between agents with round caps."""
from __future__ import annotations
import asyncpg
from typing import Callable, Awaitable
from uuid import UUID
from loguru import logger
import json

from core.config import settings
from core.enums import ThreadStatus, ThreadMode, AgentRole
from services.memory import get_thread, get_thread_messages


async def create_thread(
    pool: asyncpg.Pool, *,
    project_slug: str,
    topic: str,
    initial_question: str,
    opened_by: str,
    participants: list[str],
    mode: ThreadMode = ThreadMode.DEFAULT,
    related_feature_id: UUID | None = None,
    tg_thread_id: int | None = None,
) -> UUID:
    max_rounds = (settings.thread_deep_max_rounds if mode == ThreadMode.DEEP
                  else settings.thread_default_max_rounds)
    max_messages = (settings.thread_deep_max_messages if mode == ThreadMode.DEEP
                    else settings.thread_default_max_messages)
    budget_cap = 300 if mode == ThreadMode.DEEP else settings.default_thread_budget_cap_cents

    async with pool.acquire() as c:
        row = await c.fetchrow("""
            INSERT INTO discussion_threads
                (project_slug, topic, initial_question, opened_by, participants,
                 status, mode, max_rounds, max_messages, budget_cap_cents,
                 related_feature_id, tg_thread_id)
            VALUES ($1,$2,$3,$4,$5::jsonb,'open',$6,$7,$8,$9,$10,$11)
            RETURNING id
        """, project_slug, topic, initial_question, opened_by,
             json.dumps(participants), mode.value,
             max_rounds, max_messages, budget_cap, related_feature_id, tg_thread_id)
    thread_id = row["id"]

    # первое сообщение — initial_question от opened_by
    await add_message(pool, thread_id=thread_id, author=opened_by, content=initial_question, round_number=0)
    logger.info("Thread {} opened by {}: {}", thread_id, opened_by, topic[:80])
    return thread_id


async def add_message(
    pool: asyncpg.Pool, *,
    thread_id: UUID, author: str, content: str,
    citations: list[dict] | None = None,
    is_summary: bool = False, round_number: int = 1,
) -> int:
    async with pool.acquire() as c:
        row = await c.fetchrow("""
            INSERT INTO thread_messages (thread_id, author, content, citations, is_summary, round_number)
            VALUES ($1,$2,$3,$4::jsonb,$5,$6)
            RETURNING id
        """, thread_id, author, content, json.dumps(citations or []), is_summary, round_number)
        await c.execute("""
            UPDATE discussion_threads
            SET messages_count = messages_count + 1, updated_at = NOW()
            WHERE id=$1
        """, thread_id)
    return row["id"]


async def add_thread_cost(pool, thread_id: UUID, cost_cents: float) -> None:
    async with pool.acquire() as c:
        await c.execute("""
            UPDATE discussion_threads SET budget_used_cents = budget_used_cents + $2 WHERE id=$1
        """, thread_id, int(cost_cents))


async def is_exhausted(pool, thread_id: UUID) -> tuple[bool, str]:
    t = await get_thread(pool, thread_id)
    if not t:
        return True, "thread_not_found"
    if t["budget_used_cents"] >= t["budget_cap_cents"]:
        return True, "budget_exceeded"
    if t["messages_count"] >= t["max_messages"]:
        return True, "max_messages_reached"
    if t["rounds_completed"] >= t["max_rounds"]:
        return True, "max_rounds_reached"
    return False, ""


async def run_one_round(
    pool: asyncpg.Pool,
    thread_id: UUID,
    agent_runners: dict[str, Callable[..., Awaitable[dict]]],
) -> dict:
    """
    Один раунд обсуждения: каждый участник кроме opener'а получает шанс ответить.
    agent_runners: { agent_role: async fn(pool, thread_id, thread_history) -> {"content": str, "cost_cents": float} }
    """
    thread = await get_thread(pool, thread_id)
    if not thread:
        return {"error": "thread_not_found"}
    if thread["status"] != "open":
        return {"error": f"thread_status_{thread['status']}"}

    exhausted, reason = await is_exhausted(pool, thread_id)
    if exhausted:
        return {"error": "exhausted", "reason": reason, "needs_summary": True}

    participants = thread["participants"] if isinstance(thread["participants"], list) else json.loads(thread["participants"])
    new_round_num = thread["rounds_completed"] + 1
    speakers = []
    for role in participants:
        if role not in agent_runners:
            continue
        if role == thread["opened_by"]:
            continue  # opener уже сказал initial_question
        exhausted, _ = await is_exhausted(pool, thread_id)
        if exhausted:
            break
        messages = await get_thread_messages(pool, thread_id)
        result = await agent_runners[role](pool, thread_id, messages)
        content = result.get("content", "").strip()
        if not content or content.lower().startswith("(pass)") or content.lower().startswith("no comment"):
            speakers.append({"role": role, "content": "(passed)"})
            continue
        await add_message(pool, thread_id=thread_id, author=role, content=content, round_number=new_round_num)
        await add_thread_cost(pool, thread_id, result.get("cost_cents", 0))
        speakers.append({"role": role, "content": content[:200]})

    async with pool.acquire() as c:
        await c.execute("""
            UPDATE discussion_threads
            SET rounds_completed = rounds_completed + 1, updated_at = NOW()
            WHERE id=$1
        """, thread_id)

    return {"speakers": speakers, "round": new_round_num}


async def post_summary(
    pool: asyncpg.Pool, thread_id: UUID,
    chief_of_staff_runner: Callable[..., Awaitable[dict]],
) -> dict:
    """
    Chief of Staff обязан сформулировать варианты A/B/C для CEO когда thread исчерпан.
    """
    messages = await get_thread_messages(pool, thread_id)
    result = await chief_of_staff_runner(pool, thread_id, messages, mode="summarize_for_ceo")
    content = result.get("content", "")
    options = result.get("ceo_options")  # ожидаем что Chief вернёт structured list

    await add_message(pool, thread_id=thread_id, author=AgentRole.CHIEF_OF_STAFF.value,
                       content=content, is_summary=True, round_number=999)
    await add_thread_cost(pool, thread_id, result.get("cost_cents", 0))

    async with pool.acquire() as c:
        await c.execute("""
            UPDATE discussion_threads
            SET status='awaiting_ceo', ceo_options=$2::jsonb, updated_at=NOW()
            WHERE id=$1
        """, thread_id, json.dumps(options) if options else None)

    # создаём pending decision для CEO dashboard
    if options:
        async with pool.acquire() as c:
            t = await get_thread(pool, thread_id)
            await c.execute("""
                INSERT INTO ceo_pending_decisions
                    (project_slug, title, description, urgency, related_thread_id, choices, proposed_by)
                VALUES ($1, $2, $3, 'normal', $4, $5::jsonb, $6)
            """, t["project_slug"], t["topic"], content[:1000], thread_id,
                 json.dumps(options), AgentRole.CHIEF_OF_STAFF.value)

    return {"content": content, "options": options}


async def ceo_decide(pool: asyncpg.Pool, thread_id: UUID, decision: str) -> None:
    async with pool.acquire() as c:
        await c.execute("""
            UPDATE discussion_threads
            SET status='decided', ceo_decision=$2, decided_at=NOW(), updated_at=NOW()
            WHERE id=$1
        """, thread_id, decision)
        await c.execute("""
            UPDATE ceo_pending_decisions
            SET decided=TRUE, ceo_choice=$2, decided_at=NOW()
            WHERE related_thread_id=$1
        """, thread_id, decision)
