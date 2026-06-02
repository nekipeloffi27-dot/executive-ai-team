"""Multi-bot registry: 5 Telegram bots running in parallel."""
from __future__ import annotations
from dataclasses import dataclass
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from core.config import settings


@dataclass
class BotEntry:
    name: str             # 'chief' / 'designer' / 'cto' / 'dev' / 'research'
    token: str
    bot: Bot
    dp: Dispatcher
    avatar_role: str      # agent_role используемый для постов от этого бота


def _make(name: str, token: str, avatar: str) -> BotEntry:
    bot = Bot(token=token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    return BotEntry(name=name, token=token, bot=bot, dp=dp, avatar_role=avatar)


def build_all_bots() -> dict[str, BotEntry]:
    return {
        "chief": _make("chief", settings.tg_bot_token_chief, "chief_of_staff"),
        "designer": _make("designer", settings.tg_bot_token_designer, "designer"),
        "cto": _make("cto", settings.tg_bot_token_cto, "cto_tasking"),
        "dev": _make("dev", settings.tg_bot_token_dev, "dev_backend"),
        "research": _make("research", settings.tg_bot_token_research, "researcher"),
    }


# Маппинг agent_role → bot name
ROLE_TO_BOT = {
    "chief_of_staff": "chief",
    "designer": "designer",
    "cto_tasking": "cto",
    "cto_review": "cto",
    "dev_backend": "dev",
    "dev_frontend_web": "dev",
    "dev_frontend_mobile": "dev",
    "researcher": "research",
    "strategist": "research",
    "skill_curator": "research",
    "nl_router": "chief",
}


def bot_for_role(bots: dict[str, BotEntry], role: str) -> BotEntry:
    return bots[ROLE_TO_BOT.get(role, "chief")]


# Маппинг agent_role → telegram topic
def topic_for_role(role: str) -> int:
    return {
        "chief_of_staff": settings.tg_topic_briefing,
        "designer": settings.tg_topic_design,
        "cto_tasking": settings.tg_topic_engineering,
        "cto_review": settings.tg_topic_engineering,
        "dev_backend": settings.tg_topic_engineering,
        "dev_frontend_web": settings.tg_topic_engineering,
        "dev_frontend_mobile": settings.tg_topic_engineering,
        "researcher": settings.tg_topic_research,
        "strategist": settings.tg_topic_strategy,
        "skill_curator": settings.tg_topic_skills,
    }.get(role, settings.tg_topic_general)
