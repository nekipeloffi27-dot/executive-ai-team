"""Loads project context files into agent system prompts."""
from __future__ import annotations
from pathlib import Path
from typing import Iterable
from loguru import logger
from core.config import settings, PROJECT_ROOT


# Сопоставление alias → файл
CONTEXT_FILES = {
    "project": "PROJECT.md",
    "goal": "GOAL.md",
    "competitors": "COMPETITORS.md",
    "tech_stack": "TECH_STACK.md",
    "design_system": "DESIGN_SYSTEM.md",
    "moodboard": "MOODBOARD.md",
    "anti_references": "ANTI_REFERENCES.md",
}

# Какие файлы нужны каким ролям (минимизируем токены)
ROLE_CONTEXT = {
    "chief_of_staff": ["project", "goal", "competitors"],
    "researcher": ["project", "goal", "competitors"],
    "strategist": ["project", "goal", "competitors"],
    "designer": ["project", "design_system", "moodboard", "anti_references", "tech_stack"],
    "cto_tasking": ["project", "tech_stack"],
    "cto_review": ["project", "tech_stack"],
    "skill_curator": ["project", "goal"],
}


def current_project_slug() -> str:
    return settings.current_project_slug


def context_dir(project_slug: str | None = None) -> Path:
    slug = project_slug or current_project_slug()
    return PROJECT_ROOT / "projects" / slug / "context"


_mtime_cache: dict[str, float] = {}
_content_cache: dict[str, str] = {}


def load_file(alias: str, project_slug: str | None = None) -> str:
    """Читает файл с кешированием по mtime (hot-reload)."""
    if alias not in CONTEXT_FILES:
        return ""
    p = context_dir(project_slug) / CONTEXT_FILES[alias]
    if not p.exists():
        logger.warning("Context file not found: {}", p)
        return ""
    mtime = p.stat().st_mtime
    key = str(p)
    if _mtime_cache.get(key) == mtime and key in _content_cache:
        return _content_cache[key]
    content = p.read_text(encoding="utf-8")
    _mtime_cache[key] = mtime
    _content_cache[key] = content
    return content


def build_context_block(
    aliases: Iterable[str] | None = None,
    project_slug: str | None = None,
) -> str:
    """Собирает блок контекста для system prompt."""
    if aliases is None:
        aliases = CONTEXT_FILES.keys()
    parts = ["## Project Context\n"]
    for alias in aliases:
        content = load_file(alias, project_slug)
        if content:
            parts.append(f"### {CONTEXT_FILES[alias]}\n\n{content}\n")
    return "\n".join(parts)


def build_for_role(role: str, project_slug: str | None = None) -> str:
    aliases = ROLE_CONTEXT.get(role, ["project"])
    return build_context_block(aliases, project_slug)
