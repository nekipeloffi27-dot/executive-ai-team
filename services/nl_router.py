from __future__ import annotations
import asyncpg
import json, re
from loguru import logger
from core.config import settings
from integrations.anthropic_client import call_llm

SYSTEM = """Ты NL Router команды AI-агентов. Получаешь свободный текст CEO. Классифицируй намерение.

Возможные intents:
- `new_feature` — CEO просит реализовать новую функциональность
- `feedback_on_design` — CEO даёт фидбек на показанный мокап
- `feedback_on_code` — CEO даёт фидбек на PR
- `strategic_question` — CEO задаёт стратегический/архитектурный вопрос
- `research_request` — CEO просит что-то исследовать
- `chitchat` — приветствие, болтовня
- `status_question` — что у нас сейчас происходит, что нового
- `decision_response` — CEO отвечает на pending_decision (упоминание thread_id или key)
- `budget_question` — про бюджет
- `unknown` — не классифицируется

Также определи `target_agent` — кому маршрутизировать:
chief_of_staff / designer / cto_tasking / researcher / strategist / skill_curator

Верни JSON без markdown обёртки:
{"intent": "...", "target_agent": "...", "summary": "переформулированный запрос ≤200 знаков", "urgency": "low|normal|high"}"""


async def route_message(pool: asyncpg.Pool, text: str) -> dict:
    resp = await call_llm(
        model=settings.model_working,
        system=SYSTEM,
        messages=[{"role": "user", "content": text[:2000]}],
        max_tokens=300,
        pool=pool, agent_role="nl_router",
        operation_kind="router",
    )
    raw = resp.get("content", "{}").strip()
    if raw.startswith("```"):
        raw = "\n".join(raw.split("\n")[1:-1])
    try:
        return json.loads(raw)
    except Exception as e:
        logger.warning("NL router JSON parse failed: {} | raw={}", e, raw[:200])
        return {"intent": "unknown", "target_agent": "chief_of_staff", "summary": text[:200], "urgency": "normal"}
