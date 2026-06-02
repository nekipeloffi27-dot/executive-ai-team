"""Context commands: /context show|edit."""
from __future__ import annotations
from pathlib import Path
from aiogram import Router
from aiogram.filters import Command, CommandObject
from aiogram.types import Message
from core.config import settings, PROJECT_ROOT
from services.context import CONTEXT_FILES, context_dir


def build_router() -> Router:
    r = Router(name="context_cmd")

    @r.message(Command("context"))
    async def cmd_context(m: Message, command: CommandObject):
        if not command.args:
            await m.answer(
                "Использование:\n"
                "<code>/context list</code> — список файлов\n"
                "<code>/context show &lt;alias&gt;</code> — показать файл\n"
                "<code>/context edit &lt;alias&gt;</code> — путь для редактирования"
            )
            return
        parts = command.args.split(maxsplit=1)
        sub = parts[0].lower()
        if sub == "list":
            files = [f"• <code>{a}</code> → {f}" for a, f in CONTEXT_FILES.items()]
            await m.answer("<b>Project context files</b>\n" + "\n".join(files))
            return
        if sub in ("show", "edit") and len(parts) > 1:
            alias = parts[1].strip().lower()
            if alias not in CONTEXT_FILES:
                await m.answer(f"Неизвестный alias: {alias}")
                return
            p = context_dir() / CONTEXT_FILES[alias]
            if not p.exists():
                await m.answer(f"Файл не найден: <code>{p}</code>")
                return
            if sub == "show":
                content = p.read_text(encoding="utf-8")[:3500]
                await m.answer(f"<b>{p.name}</b>\n<pre>{content}</pre>")
            else:
                await m.answer(
                    f"Редактируй файл на VM:\n<code>{p}</code>\n"
                    f"Изменения подхватятся автоматически (hot-reload по mtime)."
                )
            return
        await m.answer("Подкоманды: list / show &lt;alias&gt; / edit &lt;alias&gt;")

    return r
