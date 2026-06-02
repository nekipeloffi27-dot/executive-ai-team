from __future__ import annotations
import json
import re
from core.config import settings
from agents.base import make_runner, AgentRegistry
from integrations.anthropic_client import call_llm
from services.context import build_for_role
from services.budget_guard import record_cost


def runner_factory(registry: AgentRegistry):
    return make_runner("chief_of_staff", settings.model_thinking, registry=registry)


async def summarize_thread_for_ceo(pool, thread_id, messages, mode="summarize_for_ceo"):
    """Вызывается из Thread Engine когда thread исчерпан."""
    history = "\n\n".join(
        f"### Round {m['round_number']} — {m['author']}\n{m['content']}"
        for m in messages
    )

    system = (
        "Ты Chief of Staff. Thread исчерпал лимиты. Сформулируй варианты A/B/C для CEO.\n"
        "В конце ответа JSON-блок:\n"
        '{"ceo_options": [{"key": "...", "label": "...", "pros": "...", "cons": "..."}]}\n\n'
        + build_for_role("chief_of_staff", settings.current_project_slug)
    )

    resp = await call_llm(
        model=settings.model_thinking,
        system=system,
        messages=[{"role": "user", "content": f"Thread history:\n\n{history}\n\nСформулируй сводку и варианты."}],
        max_tokens=2000,
        pool=pool, agent_role="chief_of_staff",
        thread_id=thread_id, operation_kind="thread_summary",
    )
    text = resp.get("content", "")

    # вырезаем JSON блок
    options = None
    m = re.search(r'\{\s*"ceo_options"\s*:\s*\[.*?\]\s*\}', text, re.DOTALL)
    if m:
        try:
            options = json.loads(m.group(0))["ceo_options"]
            text = text.replace(m.group(0), "").strip()
        except Exception:
            pass

    await record_cost(
        pool, project_slug=settings.current_project_slug, agent_role="chief_of_staff",
        thread_id=thread_id, operation_kind="thread_summary",
        model=settings.model_thinking,
        input_tokens=resp.get("usage", {}).get("input_tokens", 0),
        output_tokens=resp.get("usage", {}).get("output_tokens", 0),
        cost_cents=resp.get("usage", {}).get("cost_cents", 0),
    )

    return {"content": text, "ceo_options": options, "cost_cents": resp.get("usage", {}).get("cost_cents", 0)}
