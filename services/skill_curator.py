"""Skill Curator — weekly analysis of reflections/signals → skill proposals."""
from __future__ import annotations
import asyncpg
import json
from loguru import logger
from core.config import settings
from services.memory import get_recent_reflections, get_recent_quality_signals
from integrations.anthropic_client import call_llm

PROMPT_TEMPLATE = """Ты — Skill Curator команды AI-агентов. Анализируешь рефлексии и сигналы качества за {days} дней.

## Рефлексии агентов
{reflections}

## Сигналы качества (фидбек CEO, request_changes от CTO, redo_design и т.д.)
{signals}

---

Найди ПОВТОРЯЮЩИЕСЯ паттерны. Если паттерн встречается 3+ раз — это кандидат на новый скилл.

Возврат — JSON-массив (максимум 3 предложения):
[
  {{
    "name": "skill-name-kebab",
    "target_agent_role": "designer" / "cto_tasking" / etc,
    "rationale": "Что за паттерн, сколько раз встретился, чем поможет скилл (2-3 предложения).",
    "draft_content": "# Skill Name\\n\\n## When to apply\\n...\\n\\n## Rules\\n...\\n\\n(краткий SKILL.md, 50-150 строк)",
    "estimated_cost_impact_cents": <integer, может быть отрицательным если уменьшит redo>,
    "evidence_reflection_ids": [12, 34],
    "evidence_signal_ids": [56, 78]
  }}
]

Если паттернов с 3+ повторениями нет — возврат пустой массив [].
Не выдумывай скиллы. Если есть только разовые проблемы — возврат [].
Verbose JSON, без markdown-обёртки ```json```."""


async def run_curator(pool: asyncpg.Pool, project_slug: str, days: int = 14) -> int:
    """
    Возвращает количество созданных proposals.
    """
    reflections = await get_recent_reflections(pool, days=days, limit=100)
    signals = await get_recent_quality_signals(pool, days=days, limit=100)

    if len(reflections) + len(signals) < 5:
        logger.info("Skill Curator: not enough data ({} reflections, {} signals)",
                    len(reflections), len(signals))
        return 0

    refl_text = "\n".join(
        f"[{r['id']}] {r['agent_role']}: gap={r['knowledge_gap'][:200]} | "
        f"uncertain={r['uncertain_about'][:200]}"
        for r in reflections
    )
    sig_text = "\n".join(
        f"[{s['id']}] {s['kind']} target={s['target_agent_role']} ({s['severity']}): {s['content'][:200]}"
        for s in signals
    )

    resp = await call_llm(
        model=settings.model_thinking,
        system="Ты Skill Curator. Возвращаешь только JSON, без обёртки.",
        messages=[{"role": "user", "content": PROMPT_TEMPLATE.format(
            days=days, reflections=refl_text, signals=sig_text,
        )}],
        max_tokens=4000,
        pool=pool, agent_role="skill_curator",
        operation_kind="agentic",  # формально one_shot но логируем как curator работу
    )

    text = resp.get("content", "").strip()
    if not text or text == "[]":
        logger.info("Skill Curator: no proposals")
        return 0

    # парсим JSON
    try:
        # на всякий случай чистим markdown-обёртку если попала
        if text.startswith("```"):
            text = "\n".join(text.split("\n")[1:-1])
        proposals = json.loads(text)
    except Exception as e:
        logger.warning("Curator JSON parse failed: {}", e)
        return 0

    created = 0
    for p in proposals[:3]:  # cap 3 в неделю
        try:
            async with pool.acquire() as c:
                await c.execute("""
                    INSERT INTO skill_proposals
                        (name, target_agent_role, rationale, draft_content,
                         estimated_cost_impact_cents, evidence_reflection_ids, evidence_signal_ids)
                    VALUES ($1,$2,$3,$4,$5,$6::jsonb,$7::jsonb)
                """, p["name"][:200], p["target_agent_role"], p["rationale"][:2000],
                     p["draft_content"], p.get("estimated_cost_impact_cents") or 0,
                     json.dumps(p.get("evidence_reflection_ids", [])),
                     json.dumps(p.get("evidence_signal_ids", [])))
            created += 1
        except Exception as e:
            logger.warning("Skill proposal save failed: {}", e)

    logger.info("Skill Curator: {} proposals created", created)
    return created
