"""Dev agent orchestrator: spawn Docker sandbox, monitor, collect results."""
from __future__ import annotations
import asyncio
import json
import re
import unicodedata
from pathlib import Path
from uuid import UUID, uuid4
import asyncpg
from loguru import logger

from core.config import settings, PROJECT_ROOT
from core.enums import TaskStatus
from core.exceptions import SandboxError


# ─── Транслитерация для git-веток ────────────────────────────
_CYRILLIC_TRANSLIT = str.maketrans({
    "а":"a","б":"b","в":"v","г":"g","д":"d","е":"e","ё":"e","ж":"zh","з":"z",
    "и":"i","й":"y","к":"k","л":"l","м":"m","н":"n","о":"o","п":"p","р":"r",
    "с":"s","т":"t","у":"u","ф":"f","х":"h","ц":"c","ч":"ch","ш":"sh","щ":"sch",
    "ъ":"","ы":"y","ь":"","э":"e","ю":"yu","я":"ya",
})


def slugify_branch(title: str) -> str:
    """Возвращает безопасное ASCII-имя ветки.

    Без кириллицы (v2-баг: git refs ломались), без пробелов, lowercase, <=40 chars.
    """
    s = title.lower().translate(_CYRILLIC_TRANSLIT)
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s[:40] or "task"


def workspace_path(task_id: UUID) -> Path:
    """Хост-путь воркспейса. Строго совпадает с тем что монтируется в контейнер."""
    return Path(settings.sandbox_workspace) / str(task_id)


async def _resolve_role_files(task_type: str) -> tuple[Path, Path]:
    """Возвращает (CLAUDE.md, role_prompt.md) для типа таска."""
    role_dir = PROJECT_ROOT / "agents" / f"{task_type}_dev"
    claude_md = role_dir / "CLAUDE.md"
    role_prompt = role_dir / "role_prompt.md"
    if not claude_md.exists() or not role_prompt.exists():
        raise SandboxError(f"Role files missing for {task_type}_dev")
    return claude_md, role_prompt


def _build_task_md(task: dict, role_prompt_text: str, claude_md_text: str = "") -> str:
    """Формирует TASK.md из готового плана от CTO.

    Это критично для эффективности dev-агента: он получает не «сделай это», а
    конкретный список файлов + что именно поменять.
    """
    affected = task.get("affected_files") or []
    changes = task.get("changes_per_file") or []
    criteria = task.get("acceptance_criteria") or []
    api_contract = task.get("api_contract")

    parts = [
        f"# {task['title']}\n",
        "## HARD RULES — read first\n",
        "1. **DO NOT modify the existing `CLAUDE.md` / `PROJECT.md` / `README.md` / any root-level docs**. "
        "They are the source of truth for this project — leave them alone unless the task explicitly asks "
        "to update documentation.\n",
        "2. **Make REAL code changes** that fulfil the acceptance criteria below. "
        "Do not stop after editing only docs/configs unless the task is literally about docs/configs.\n",
        "3. **If the task description is too vague to act on** — DO NOT invent work. "
        "Instead, create a single `EXEC_TEAM_QUESTIONS.md` file in the repo root listing your blocking questions, "
        "commit it, and exit. The PR will signal to CEO that clarification is needed.\n",
        "4. Use existing project patterns. Read `PROJECT.md`, `packages/<your-package>/`, and any nested "
        "`CLAUDE.md` (e.g. `packages/web/halo-ds/CLAUDE.md`) as context.\n",
        "5. Do not add new top-level dependencies unless TASK.md explicitly lists them.\n",
        "6. Write tests for new code in the project's existing test framework.\n",
        "7. If you can't complete a criterion, document why in the commit message — don't fake it.\n",
        "\n## Task description\n\n",
        task.get("description", "") or "(нет описания — см. attachments)",
        "\n\n## Role-specific guidance\n",
        role_prompt_text,
    ]
    if claude_md_text:
        parts.append("\n## Tech-stack rules (your operating manual for this role)\n")
        parts.append(claude_md_text)

    parts.append("\n## Affected files\n")
    if affected:
        for f in affected:
            parts.append(f"- `{f}`")
    else:
        parts.append("_Не указаны явно. Определи сам из описания + attachments + структуры репо._")
    parts.append("\n## Changes per file\n")
    if changes:
        for ch in changes:
            parts.append(f"### `{ch.get('path','?')}`\n\n{ch.get('what','')}\n")
    else:
        parts.append("_Не указаны явно. Декомпозируй описание сам._")
    if api_contract:
        parts.append("## API contract\n\n```json")
        parts.append(json.dumps(api_contract, indent=2, ensure_ascii=False))
        parts.append("```")
    parts.append("\n## Acceptance criteria\n")
    if criteria:
        for c in criteria:
            parts.append(f"- [ ] {c}")
    else:
        parts.append("- [ ] Реализация описания (см. выше + attachments)")
        parts.append("- [ ] PR с понятным заголовком и описанием")
    return "\n".join(parts)


async def run_dev_agent(
    pool: asyncpg.Pool, *,
    task_id: UUID,
    task: dict,             # содержит title, description, type, affected_files, ...
    repo_url: str,          # с встроенным GITHUB_TOKEN
    base_branch: str = "main",
) -> dict:
    """Запускает sandbox для одного таска.

    Возвращает {pr_url, pr_number, branch_name, logs_path, success, error}.
    """
    task_type = task["type"]                        # backend|frontend_web|frontend_mobile
    complexity = task.get("complexity", "medium")
    branch_name = f"feat/{slugify_branch(task['title'])}-{str(task_id)[:8]}"

    # ─── Подготовка хост-воркспейса ────────────────────────
    host_ws = workspace_path(task_id)
    host_ws.mkdir(parents=True, exist_ok=True)
    task_dir = host_ws / "task"
    task_dir.mkdir(exist_ok=True)

    claude_md_src, role_prompt_src = await _resolve_role_files(task_type)
    role_prompt_text = role_prompt_src.read_text(encoding="utf-8")
    claude_md_text = claude_md_src.read_text(encoding="utf-8")

    # CLAUDE.md инлайнится внутрь TASK.md — НЕ копируется в корень репо продукта,
    # иначе перезаписал бы существующий PROJECT.md / CLAUDE.md проекта.
    (task_dir / "TASK.md").write_text(
        _build_task_md(task, role_prompt_text, claude_md_text), encoding="utf-8"
    )
    (task_dir / "pr-body.md").write_text(
        f"## Task\n{task['title']}\n\n## Description\n{task['description']}\n\n"
        f"## Acceptance Criteria\n" + "\n".join(f"- [ ] {c}" for c in task.get("acceptance_criteria") or []) +
        f"\n\n_Generated by exec-team {task_type}_dev agent._",
        encoding="utf-8",
    )

    # ─── Выбор модели по сложности ─────────────────────────
    model_by_complexity = {
        "simple": "claude-haiku-4-5",
        "medium": "claude-sonnet-4-6",
        "complex": "claude-sonnet-4-6",
    }
    claude_model = model_by_complexity.get(complexity, settings.sandbox_claude_model)
    max_turns = {"simple": 30, "medium": 50, "complex": 80}.get(complexity, settings.sandbox_claude_code_max_turns)

    # ─── docker run ────────────────────────────────────────
    container_name = f"exec-dev-{task_type}-{str(task_id)[:8]}-{uuid4().hex[:6]}"
    host_skills_dir = str(Path(settings.skills_dir).resolve())

    # CRITICAL: host_ws и /workspace внутри контейнера совпадают по структуре.
    # Внутри контейнера entrypoint работает с /workspace/repo (репозиторий) и /workspace/task (наши файлы).
    docker_cmd = [
        "docker", "run",
        "--name", container_name,
        "--rm",
        "-v", f"{host_ws}:/workspace",
        "-v", f"{host_skills_dir}/{task_type}_dev:/workspace/skills:ro",
        "-e", f"TASK_ID={task_id}",
        "-e", f"BRANCH_NAME={branch_name}",
        "-e", f"REPO_URL={repo_url}",
        "-e", f"BASE_BRANCH={base_branch}",
        "-e", f"ANTHROPIC_API_KEY={settings.anthropic_api_key}",
        "-e", f"GITHUB_TOKEN={settings.github_token}",
        "-e", f"MAX_TURNS={max_turns}",
        "-e", f"CLAUDE_MODEL={claude_model}",
        settings.sandbox_image,
    ]

    logger.info("Starting sandbox container {} for task {}", container_name, task_id)

    proc = await asyncio.create_subprocess_exec(
        *docker_cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    try:
        stdout, stderr = await asyncio.wait_for(
            proc.communicate(),
            timeout=settings.sandbox_timeout_seconds,
        )
        rc = proc.returncode
    except asyncio.TimeoutError:
        logger.error("Sandbox {} timed out after {}s — killing", container_name, settings.sandbox_timeout_seconds)
        try:
            kill_proc = await asyncio.create_subprocess_exec("docker", "kill", container_name)
            await kill_proc.wait()
        except Exception as e:
            logger.warning("Failed to kill container {}: {}", container_name, e)
        stdout, stderr = b"", b"TIMEOUT"
        rc = 124

    # ─── Сохраняем логи ───────────────────────────────────
    (task_dir / "stdout.log").write_bytes(stdout)
    (task_dir / "stderr.log").write_bytes(stderr)

    # ─── Парсим результат ─────────────────────────────────
    pr_url_file = task_dir / "pr-url.txt"
    result_file = task_dir / "result.txt"
    pr_url = pr_url_file.read_text(encoding="utf-8").strip() if pr_url_file.exists() else None
    no_changes = result_file.exists() and result_file.read_text(encoding="utf-8").strip() == "NO_CHANGES"

    if rc != 0 and not pr_url:
        return {
            "success": False,
            "error": f"Sandbox exited with code {rc}",
            "stderr_tail": stderr.decode("utf-8", errors="replace")[-2000:],
            "logs_path": str(task_dir),
            "branch_name": branch_name,
        }

    if no_changes:
        return {
            "success": False,
            "error": "Dev agent did not produce any changes",
            "logs_path": str(task_dir),
            "branch_name": branch_name,
        }

    pr_number = None
    if pr_url:
        m = re.search(r"/pull/(\d+)", pr_url)
        if m:
            pr_number = int(m.group(1))

    return {
        "success": True,
        "pr_url": pr_url,
        "pr_number": pr_number,
        "branch_name": branch_name,
        "logs_path": str(task_dir),
    }


async def cancel_sandbox(task_id: UUID) -> None:
    """Останавливает sandbox-контейнер для таска (если запущен)."""
    # Имена контейнеров содержат task_id префикс
    proc = await asyncio.create_subprocess_exec(
        "sh", "-c",
        f"docker ps --filter 'name=exec-dev-' --filter 'name={str(task_id)[:8]}' --format '{{{{.Names}}}}' | xargs -r docker kill",
        stdout=asyncio.subprocess.PIPE,
    )
    await proc.communicate()
