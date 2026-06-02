from __future__ import annotations
import asyncpg
from loguru import logger
from core.config import settings
from integrations.anthropic_client import call_llm

PROMPT = """Ты — {role}. Только что ты завершил задачу.

## Задача
{task}

## Что сделал
{output}

## Результат
{outcome}

---

Отрефлексируй честно для своих заметок (не для отчёта). Структура — ровно 4 секции:

**Went well:** ...
**Uncertain about:** ...
**Knowledge gap:** ...
**Would do differently:** ...

Кратко и конкретно. Без общих слов. Каждая секция 1-3 предложения."""


async def reflect(
    pool: asyncpg.Pool, *,
    agent_role: str, task_description: str, output: str,
    outcome: str = "completed",
    feature_id=None, task_id=None, thread_id=None,
) -> int | None:
    if not settings.reflection_enabled:
        return None
    resp = await call_llm(
        model=settings.model_reflection,
        system="Ты помогаешь агенту делать честную короткую рефлексию.",
        messages=[{"role": "user", "content": PROMPT.format(
            role=agent_role, task=task_description[:1000],
            output=output[:2000], outcome=outcome,
        )}],
        max_tokens=600,
        pool=pool, agent_role=agent_role,
        feature_id=feature_id, task_id=task_id, thread_id=thread_id,
        operation_kind="reflection",
    )
    text = resp.get("content", "")
    if not text:
        return None

    # парсим секции
    sections = {"went_well": "", "uncertain_about": "", "knowledge_gap": "", "would_do_differently": ""}
    current = None
    for line in text.splitlines():
        l = line.strip()
        if l.lower().startswith("**went well"):
            current = "went_well"; sections[current] = l.split(":", 1)[1].strip() if ":" in l else ""
        elif l.lower().startswith("**uncertain"):
            current = "uncertain_about"; sections[current] = l.split(":", 1)[1].strip() if ":" in l else ""
        elif l.lower().startswith("**knowledge gap"):
            current = "knowledge_gap"; sections[current] = l.split(":", 1)[1].strip() if ":" in l else ""
        elif l.lower().startswith("**would do"):
            current = "would_do_differently"; sections[current] = l.split(":", 1)[1].strip() if ":" in l else ""
        elif current and l:
            sections[current] += " " + l

    try:
        async with pool.acquire() as c:
            row = await c.fetchrow("""
                INSERT INTO agent_reflections
                    (agent_role, feature_id, task_id, thread_id, task_description,
                     went_well, uncertain_about, knowledge_gap, would_do_differently, outcome)
                VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10) RETURNING id
            """, agent_role, feature_id, task_id, thread_id, task_description[:500],
                 sections["went_well"][:1000], sections["uncertain_about"][:1000],
                 sections["knowledge_gap"][:1000], sections["would_do_differently"][:1000],
                 outcome)
        return row["id"]
    except Exception as e:
        logger.warning("Reflection save failed: {}", e)
        return None
