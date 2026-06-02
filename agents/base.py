"""Base agentic runner. Each agent has its own runner that wires up tools + system prompt."""
from __future__ import annotations
import asyncpg
from pathlib import Path
from typing import Callable, Awaitable
from loguru import logger

from core.config import settings, PROJECT_ROOT
from core.enums import AgentRole
from services.context import build_for_role
from services.memory import get_active_decisions, format_decisions_for_prompt
from services.budget_guard import can_run, record_cost
from integrations.anthropic_client import agentic_loop, call_llm
from agents.tools import memory_tools, thread_tools, codebase_tools, research_tools


def load_system_prompt(role: str) -> str:
    p = PROJECT_ROOT / "agents" / role / "system_prompt.md"
    if not p.exists():
        logger.warning("System prompt not found: {}", p)
        return ""
    return p.read_text(encoding="utf-8")


def load_skills_for(role: str) -> str:
    if not settings.skills_enabled:
        return ""
    chunks = []
    skills_root = Path(settings.skills_dir)
    for base in (skills_root / "common", skills_root / role):
        if not base.exists():
            continue
        for skill_dir in sorted(base.iterdir()):
            sk = skill_dir / "SKILL.md"
            if sk.exists():
                chunks.append(f'<skill name="{skill_dir.name}">\n{sk.read_text(encoding="utf-8")}\n</skill>')
    return "\n\n".join(chunks)


def build_system_blocks(role: str, project_slug: str) -> list[dict]:
    """Возвращает system как list-of-blocks с cache_control на последнем (через _apply_prompt_cache)."""
    # 1. Base prompt
    base = load_system_prompt(role)
    # 2. Context (PROJECT.md etc) per role
    ctx = build_for_role(role, project_slug)
    # 3. Active decisions
    return [{
        "type": "text",
        "text": (
            f"{base}\n\n"
            f"---\n\n{ctx}\n\n"
            f"---\n\n## Skills\n\n{load_skills_for(role)}"
        ),
    }]


def get_max_iterations(role: str) -> int:
    return {
        "designer": settings.agentic_max_iterations_designer,
        "cto_tasking": settings.agentic_max_iterations_cto,
        "cto_review": settings.agentic_max_iterations_cto,
        "researcher": settings.agentic_max_iterations_researcher,
        "strategist": settings.agentic_max_iterations_strategist,
        "chief_of_staff": settings.agentic_max_iterations_chief,
        "skill_curator": settings.agentic_max_iterations_curator,
    }.get(role, 10)


def get_tools_for(role: str, registry: "AgentRegistry | None" = None) -> tuple[list[dict], Callable]:
    """
    Возвращает (tools_list, tool_executor).
    Каждая роль получает свой набор tools.
    """
    tools: list[dict] = []
    tools += memory_tools.tool_definitions()
    tools += thread_tools.tool_definitions()
    # ask_agent — у всех кроме самих dev'ов (которые работают в sandbox)
    from agents.tools import ask_agent_tool
    tools += ask_agent_tool.tool_definitions()

    if role in {"designer", "cto_tasking", "cto_review"}:
        tools += codebase_tools.tool_definitions()
    if role == "researcher":
        tools += research_tools.tool_definitions()

    return tools, None  # executor строится в make_runner


def make_runner(
    role: str, model: str, registry: "AgentRegistry | None" = None,
) -> Callable[..., Awaitable[dict]]:
    """
    Возвращает async-функцию-раннер для агента.
    Сигнатура раннера: (pool, user_message, *, project_slug, feature_id=None, ...) -> dict
    """
    max_iter = get_max_iterations(role)
    tools, _ = get_tools_for(role)

    async def runner(
        pool: asyncpg.Pool, user_message: str, *,
        project_slug: str | None = None,
        feature_id=None, task_id=None, thread_id=None,
        extra_context: str = "",
        operation_kind: str = "agentic",
    ) -> dict:
        slug = project_slug or settings.current_project_slug

        # бюджетная проверка для non-critical
        allowed, reason = await can_run(pool, slug, role)
        if not allowed:
            logger.info("Agent {} blocked by budget: {}", role, reason)
            return {"content": "", "blocked": True, "reason": reason, "cost_cents": 0}

        system_blocks = build_system_blocks(role, slug)
        if extra_context:
            system_blocks[0]["text"] += f"\n\n---\n\n## Additional Context\n\n{extra_context}"

        messages = [{"role": "user", "content": user_message}]

        async def tool_executor(name: str, args: dict) -> str:
            try:
                if name in {"read_decisions", "read_roadmap", "read_recent_reflections",
                            "read_research_findings", "read_quality_signals"}:
                    return await memory_tools.execute(pool, slug, name, args)
                if name in {"open_thread", "read_thread", "post_to_thread"}:
                    return await thread_tools.execute(pool, slug, name, args, calling_agent=role)
                if name in {"codebase_list", "codebase_read", "codebase_grep"}:
                    return await codebase_tools.execute(name, args)
                if name == "ask_agent" and registry:
                    from agents.tools import ask_agent_tool
                    return await ask_agent_tool.execute(pool, slug, name, args, registry)
                return f"Tool {name} not handled"
            except Exception as e:
                logger.exception("Tool {} executor failed", name)
                return f"Error: {e}"

        resp = await agentic_loop(
            model=model,
            system=system_blocks,
            messages=messages,
            tools=tools,
            tool_executor=tool_executor,
            max_iterations=max_iter,
            max_tokens=4000,
            pool=pool, agent_role=role,
            feature_id=feature_id, task_id=task_id, thread_id=thread_id,
        )

        # record cost attribution
        usage = resp.get("usage") or {}
        await record_cost(
            pool, project_slug=slug, agent_role=role,
            feature_id=feature_id, task_id=task_id, thread_id=thread_id,
            operation_kind=operation_kind, model=model,
            input_tokens=usage.get("input_tokens", 0),
            output_tokens=usage.get("output_tokens", 0),
            cost_cents=usage.get("cost_cents", 0),
        )

        return {
            "content": resp.get("content", ""),
            "iterations": resp.get("iterations", 0),
            "cost_cents": usage.get("cost_cents", 0),
            "error": resp.get("error"),
        }

    return runner


class AgentRegistry:
    """Holds runners for all agents. Used by ask_agent tool and bot handlers."""

    def __init__(self):
        self._runners: dict[str, Callable] = {}

    def register(self, role: str, runner: Callable) -> None:
        self._runners[role] = runner

    def get_oneshot_runner(self, role: str) -> Callable | None:
        return self._runners.get(role)


def build_registry() -> AgentRegistry:
    """Создаёт и наполняет registry всеми 8 агентами."""
    reg = AgentRegistry()
    # сначала создаём, потом передаём registry внутрь runner'ов через замыкание
    for role, model in [
        ("chief_of_staff", settings.model_thinking),
        ("researcher", settings.model_thinking),
        ("strategist", settings.model_thinking),
        ("designer", settings.model_thinking),
        ("cto_tasking", settings.model_thinking),
        ("cto_review", settings.model_thinking),
        ("skill_curator", settings.model_thinking),
    ]:
        reg.register(role, make_runner(role, model, registry=reg))
    return reg
