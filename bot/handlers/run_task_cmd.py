"""Run dev agents on a free-form spec — text + attachments (html/screenshots) + optional JSON tasks."""
from __future__ import annotations
import json
import re
from pathlib import Path
from uuid import uuid4
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, Document, PhotoSize
from loguru import logger

from core.config import settings
from core.db import get_pool
from agents.dev.runner import run_dev_agent, workspace_path


# эвристики для определения типа таски
_BACKEND_HINTS = re.compile(
    r"\b(api|endpoint|router|alembic|migration|schema|backend|бэк|маршрут|sql|asyncpg|sqlalchemy|fastapi)\b",
    re.IGNORECASE,
)
_FRONTEND_HINTS = re.compile(
    r"\b(экран|welcome|мокап|design|tailwind|компонент|page\.tsx|фронт|next\.js|react|halo|ui)\b",
    re.IGNORECASE,
)


def _infer_task_type(text: str, has_html: bool) -> str:
    if has_html:
        return "frontend_web"
    if _BACKEND_HINTS.search(text or ""):
        return "backend"
    if _FRONTEND_HINTS.search(text or ""):
        return "frontend_web"
    return "frontend_web"  # default — большинство фич UI-первые


def _extract_json_tasks(text: str) -> list[dict] | None:
    """Ищем самый большой JSON-объект с ключом 'tasks'."""
    if not text:
        return None
    # сначала ищем все json-кандидаты (с балансировкой скобок — упрощённо через regex)
    candidates: list[str] = []
    # уберём markdown-обёртку ```json ... ```
    cleaned = re.sub(r"```(?:json)?\s*\n?", "", text)
    cleaned = cleaned.replace("```", "")
    # жадно ищем {...} блоки
    stack = []
    start = -1
    for i, ch in enumerate(cleaned):
        if ch == "{":
            if not stack:
                start = i
            stack.append(ch)
        elif ch == "}" and stack:
            stack.pop()
            if not stack and start >= 0:
                candidates.append(cleaned[start : i + 1])
                start = -1
    candidates.sort(key=len, reverse=True)
    for c in candidates:
        try:
            obj = json.loads(c)
        except Exception:
            continue
        if isinstance(obj, dict) and isinstance(obj.get("tasks"), list) and obj["tasks"]:
            return obj["tasks"]
    return None


async def _download_attachments(msg: Message, dest: Path) -> list[Path]:
    """Скачивает все document/photo из msg в dest. Возвращает список путей."""
    saved: list[Path] = []
    if not msg:
        return saved
    dest.mkdir(parents=True, exist_ok=True)

    if msg.document:
        d: Document = msg.document
        fname = (d.file_name or f"document-{d.file_unique_id}.bin")
        fname = Path(fname).name  # защита от path-traversal
        target = dest / fname
        try:
            file = await msg.bot.get_file(d.file_id)
            await msg.bot.download_file(file.file_path, destination=str(target))
            saved.append(target)
        except Exception as e:
            logger.warning("Failed to download document {}: {}", fname, e)

    if msg.photo:
        # photo приходит списком разрешений, берём максимум
        biggest: PhotoSize = msg.photo[-1]
        target = dest / f"photo-{biggest.file_unique_id}.jpg"
        try:
            file = await msg.bot.get_file(biggest.file_id)
            await msg.bot.download_file(file.file_path, destination=str(target))
            saved.append(target)
        except Exception as e:
            logger.warning("Failed to download photo: {}", e)

    return saved


def build_router() -> Router:
    r = Router(name="run_task_cmd")

    @r.message(Command("run_task"))
    async def cmd_run_task(m: Message):
        # ── 1. Собираем текст: команда + caption + reply.text + reply.caption ──
        parts: list[str] = []
        if m.text:
            tail = m.text.split(maxsplit=1)
            if len(tail) > 1:
                parts.append(tail[1])
        if m.caption:
            parts.append(m.caption)
        if m.reply_to_message:
            if m.reply_to_message.text:
                parts.append(m.reply_to_message.text)
            if m.reply_to_message.caption:
                parts.append(m.reply_to_message.caption)
        full_text = "\n\n".join(p for p in parts if p).strip()

        # ── 2. Скачиваем attachments из reply + текущего сообщения ──
        temp_id = uuid4()
        temp_attach_dir = Path(settings.sandbox_workspace) / "ad-hoc-attachments" / str(temp_id)
        attachments: list[Path] = []
        try:
            attachments += await _download_attachments(m.reply_to_message, temp_attach_dir)
            attachments += await _download_attachments(m, temp_attach_dir)
        except Exception as e:
            logger.exception("Failed to download attachments")
            await m.answer(f"⚠️ Не смог скачать вложения: {e}")
            return

        # подмешиваем в текст содержимое текстовых аттачментов — для поиска JSON tasks
        attachment_text_dump = ""
        for p in attachments:
            if p.suffix.lower() in {".txt", ".json", ".md"}:
                try:
                    attachment_text_dump += "\n\n" + p.read_text(encoding="utf-8", errors="replace")
                except Exception:
                    pass

        # ── 3. Пробуем извлечь готовый JSON-план от CTO ──
        tasks_spec = _extract_json_tasks(full_text + "\n\n" + attachment_text_dump)

        if not tasks_spec:
            if not full_text and not attachments:
                await m.answer(
                    "Использование:\n"
                    "1) <code>/run_task &lt;описание задачи&gt;</code>\n"
                    "2) Reply на файл от Designer/CTO + <code>/run_task</code>\n"
                    "3) Прикрепи файл/скриншот, в caption начни с <code>/run_task</code>\n"
                    "4) <code>/run_task</code> + JSON с ключом <code>tasks</code> в тексте — готовый CTO-план"
                )
                return
            has_html = any(p.suffix.lower() in {".html", ".htm"} for p in attachments)
            first_line = (full_text.splitlines() or ["Ad-hoc task"])[0]
            tasks_spec = [{
                "type": _infer_task_type(full_text, has_html),
                "complexity": "medium",
                "title": first_line[:140],
                "description": full_text or "См. attachments",
                "affected_files": [],
                "changes_per_file": [],
                "acceptance_criteria": [
                    "Реализовать описание из TASK.md и attachments",
                    "Открыть PR с понятным описанием",
                ],
            }]

        pool = get_pool()
        has_html_global = any(p.suffix.lower() in {".html", ".htm"} for p in attachments)

        # ── 4. Создаём feature-обёртку ──
        first_title = tasks_spec[0].get("title", "Ad-hoc tasks")
        async with pool.acquire() as c:
            feat_row = await c.fetchrow("""
                INSERT INTO features (project_slug, title, description, state, mode)
                VALUES ($1, $2, $3, 'coding', 'new')
                RETURNING id
            """,
                settings.current_project_slug,
                first_title[:200],
                (full_text or first_title)[:5000],
            )
            feature_id = feat_row["id"]

        await m.answer(
            f"🚀 Фича <code>{str(feature_id)[:8]}</code> создана.\n"
            f"Тасок: <b>{len(tasks_spec)}</b> · Вложений: <b>{len(attachments)}</b>\n"
            f"Запускаю dev-агентов в sandbox последовательно..."
        )

        repo_url = (
            f"https://x-access-token:{settings.github_token}"
            f"@github.com/{settings.product_repo}.git"
        )

        # ── 5. Прогоняем по таскам ──
        for idx, task_spec in enumerate(tasks_spec, 1):
            ttype = task_spec.get("type") or _infer_task_type(full_text, has_html_global)
            title = task_spec.get("title", f"Task {idx}")
            complexity = task_spec.get("complexity", "medium")

            async with pool.acquire() as c:
                trow = await c.fetchrow("""
                    INSERT INTO tasks
                    (feature_id, type, status, complexity, title, description,
                     affected_files, changes_per_file, acceptance_criteria, api_contract)
                    VALUES ($1, $2, 'in_progress', $3, $4, $5, $6::jsonb, $7::jsonb, $8::jsonb, $9::jsonb)
                    RETURNING id
                """,
                    feature_id, ttype, complexity, title[:200],
                    (task_spec.get("description", "") or "")[:5000],
                    json.dumps(task_spec.get("affected_files") or []),
                    json.dumps(task_spec.get("changes_per_file") or []),
                    json.dumps(task_spec.get("acceptance_criteria") or []),
                    json.dumps(task_spec["api_contract"]) if task_spec.get("api_contract") else None,
                )
                task_id = trow["id"]

            # ── копируем attachments внутрь task-workspace ──
            host_ws = workspace_path(task_id)
            attach_in_task = host_ws / "task" / "attachments"
            attach_in_task.mkdir(parents=True, exist_ok=True)
            attach_descriptions: list[str] = []
            for p in attachments:
                dest = attach_in_task / p.name
                try:
                    dest.write_bytes(p.read_bytes())
                    attach_descriptions.append(
                        f"- `attachments/{p.name}` ({p.stat().st_size} bytes)"
                    )
                except Exception as e:
                    logger.warning("Failed to copy attachment {} for task {}: {}", p, task_id, e)

            # Дополняем description ссылками на attachments — попадёт в TASK.md
            if attach_descriptions:
                extra = (
                    "\n\n## Attachments (примонтированы в /workspace/task/attachments/)\n"
                    + "\n".join(attach_descriptions)
                    + "\n\nИспользуй эти файлы как референс. HTML-мокапы от дизайнера — это визуальная спецификация, "
                      "не плагин для production. Извлекай разметку/композицию, но реализуй на проектном стеке "
                      "(Next.js + Halo DS если frontend, FastAPI + SQLAlchemy если backend)."
                )
                task_spec["description"] = (task_spec.get("description", "") + extra)[:8000]
                async with pool.acquire() as c:
                    await c.execute(
                        "UPDATE tasks SET description=$2, updated_at=NOW() WHERE id=$1",
                        task_id, task_spec["description"],
                    )

            await m.answer(
                f"🐳 [{idx}/{len(tasks_spec)}] <b>{title[:140]}</b>\n"
                f"type=<code>{ttype}</code> complexity=<code>{complexity}</code>\n"
                f"task=<code>{str(task_id)[:8]}</code> attachments=<b>{len(attach_descriptions)}</b>\n"
                f"⏳ Sandbox работает (5-30 мин)..."
            )

            try:
                result = await run_dev_agent(
                    pool,
                    task_id=task_id,
                    task={**task_spec, "title": title, "type": ttype, "complexity": complexity},
                    repo_url=repo_url,
                )
            except Exception as e:
                logger.exception("Sandbox failed for task {}", task_id)
                async with pool.acquire() as c:
                    await c.execute(
                        "UPDATE tasks SET status='failed', updated_at=NOW() WHERE id=$1", task_id
                    )
                await m.answer(f"❌ [{idx}/{len(tasks_spec)}] Sandbox упал: {str(e)[:500]}")
                continue

            if result.get("success"):
                async with pool.acquire() as c:
                    await c.execute("""
                        UPDATE tasks
                        SET status='pr_open', pr_url=$2, pr_number=$3, branch_name=$4, updated_at=NOW()
                        WHERE id=$1
                    """,
                        task_id, result.get("pr_url"), result.get("pr_number"), result.get("branch_name"),
                    )
                await m.answer(
                    f"✅ [{idx}/{len(tasks_spec)}] PR: {result.get('pr_url')}\n"
                    f"Branch: <code>{result.get('branch_name')}</code>"
                )
            else:
                async with pool.acquire() as c:
                    await c.execute(
                        "UPDATE tasks SET status='failed', updated_at=NOW() WHERE id=$1", task_id
                    )
                err = (result.get("error") or "unknown")[:600]
                await m.answer(
                    f"❌ [{idx}/{len(tasks_spec)}] Failed: {err}\n"
                    f"Logs: <code>{result.get('logs_path')}</code>"
                )

        # ── 6. Завершаем feature ──
        async with pool.acquire() as c:
            await c.execute(
                "UPDATE features SET state='review', updated_at=NOW() WHERE id=$1",
                feature_id,
            )
        await m.answer(
            f"🏁 Все задачи обработаны. Фича <code>{str(feature_id)[:8]}</code> → state <code>review</code>.\n"
            f"Глянь PR-ы выше, замержи руками если ок."
        )

    return r
