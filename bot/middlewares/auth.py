"""Whitelist auth middleware."""
from __future__ import annotations
from typing import Any, Callable, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message
from loguru import logger
from core.config import settings


class WhitelistMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        msg = event if isinstance(event, Message) else getattr(event, "message", None)
        if msg is None:
            return await handler(event, data)
        user_id = msg.from_user.id if msg.from_user else None
        if not user_id or user_id not in settings.allowed_user_ids:
            logger.warning("Blocked message from unauthorized user_id={}", user_id)
            return
        return await handler(event, data)
