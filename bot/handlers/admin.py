"""Admin commands: /start /ping /chatid /version."""
from __future__ import annotations
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from core.config import settings


def build_router(bot_name: str) -> Router:
    r = Router(name=f"admin_{bot_name}")

    @r.message(Command("start"))
    async def cmd_start(m: Message):
        await m.answer(
            f"<b>Executive Team — {bot_name}</b>\n\n"
            f"Project: <code>{settings.current_project_slug}</code>\n"
            "Use /help to see commands."
        )

    @r.message(Command("ping"))
    async def cmd_ping(m: Message):
        await m.answer(f"pong from {bot_name}")

    @r.message(Command("chatid"))
    async def cmd_chatid(m: Message):
        thread = m.message_thread_id
        await m.answer(
            f"chat_id: <code>{m.chat.id}</code>\n"
            f"user_id: <code>{m.from_user.id}</code>\n"
            f"thread_id: <code>{thread}</code>"
        )

    @r.message(Command("version"))
    async def cmd_version(m: Message):
        await m.answer(f"executive-ai-team v3 ({bot_name})")

    return r
