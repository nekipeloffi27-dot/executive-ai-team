"""Application configuration via pydantic-settings."""
from __future__ import annotations
from pathlib import Path
from typing import Literal
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Anthropic
    anthropic_api_key: str = Field(alias="ANTHROPIC_API_KEY")
    anthropic_proxy_url: str = Field(default="", alias="ANTHROPIC_PROXY_URL")
    anthropic_timeout_seconds: int = Field(default=900, alias="ANTHROPIC_TIMEOUT_SECONDS")
    anthropic_max_retries: int = Field(default=3, alias="ANTHROPIC_MAX_RETRIES")
    prompt_cache_enabled: bool = Field(default=True, alias="PROMPT_CACHE_ENABLED")

    model_thinking: str = Field(default="claude-opus-4-7", alias="MODEL_THINKING")
    model_working: str = Field(default="claude-sonnet-4-6", alias="MODEL_WORKING")
    model_cheap: str = Field(default="claude-haiku-4-5", alias="MODEL_CHEAP")
    model_reflection: str = Field(default="claude-haiku-4-5", alias="MODEL_REFLECTION")

    # Telegram
    tg_bot_token_chief: str = Field(alias="TG_BOT_TOKEN_CHIEF")
    tg_bot_token_designer: str = Field(alias="TG_BOT_TOKEN_DESIGNER")
    tg_bot_token_cto: str = Field(alias="TG_BOT_TOKEN_CTO")
    tg_bot_token_dev: str = Field(alias="TG_BOT_TOKEN_DEV")
    tg_bot_token_research: str = Field(alias="TG_BOT_TOKEN_RESEARCH")

    tg_group_id: int = Field(alias="TG_GROUP_ID")
    tg_allowed_users: str = Field(default="", alias="TG_ALLOWED_USERS")  # comma-separated

    tg_topic_briefing: int = Field(default=0, alias="TG_TOPIC_BRIEFING")
    tg_topic_decisions: int = Field(default=0, alias="TG_TOPIC_DECISIONS")
    tg_topic_research: int = Field(default=0, alias="TG_TOPIC_RESEARCH")
    tg_topic_strategy: int = Field(default=0, alias="TG_TOPIC_STRATEGY")
    tg_topic_design: int = Field(default=0, alias="TG_TOPIC_DESIGN")
    tg_topic_engineering: int = Field(default=0, alias="TG_TOPIC_ENGINEERING")
    tg_topic_skills: int = Field(default=0, alias="TG_TOPIC_SKILLS")
    tg_topic_general: int = Field(default=0, alias="TG_TOPIC_GENERAL")

    # Database
    database_url: str = Field(alias="DATABASE_URL")
    db_password: str = Field(default="", alias="DB_PASSWORD")
    redis_url: str = Field(default="redis://redis:6379/0", alias="REDIS_URL")

    # GitHub
    github_token: str = Field(default="", alias="GITHUB_TOKEN")
    github_user: str = Field(default="", alias="GITHUB_USER")
    product_repo: str = Field(default="", alias="PRODUCT_REPO")

    # Project
    current_project_slug: str = Field(default="moy-kosmetolog", alias="CURRENT_PROJECT_SLUG")

    # Budget
    monthly_team_budget_usd: int = Field(default=150, alias="MONTHLY_TEAM_BUDGET_USD")
    hard_stop_threshold_pct: int = Field(default=80, alias="HARD_STOP_THRESHOLD_PCT")
    default_feature_budget_cap_cents: int = Field(default=500, alias="DEFAULT_FEATURE_BUDGET_CAP_CENTS")
    default_thread_budget_cap_cents: int = Field(default=100, alias="DEFAULT_THREAD_BUDGET_CAP_CENTS")

    # Agentic caps
    agentic_max_iterations_designer: int = Field(default=20, alias="AGENTIC_MAX_ITERATIONS_DESIGNER")
    agentic_max_iterations_cto: int = Field(default=20, alias="AGENTIC_MAX_ITERATIONS_CTO")
    agentic_max_iterations_researcher: int = Field(default=20, alias="AGENTIC_MAX_ITERATIONS_RESEARCHER")
    agentic_max_iterations_strategist: int = Field(default=20, alias="AGENTIC_MAX_ITERATIONS_STRATEGIST")
    agentic_max_iterations_chief: int = Field(default=5, alias="AGENTIC_MAX_ITERATIONS_CHIEF")
    agentic_max_iterations_curator: int = Field(default=10, alias="AGENTIC_MAX_ITERATIONS_CURATOR")

    # Sandbox
    sandbox_image: str = Field(default="executive-ai-team-dev-sandbox:latest", alias="SANDBOX_IMAGE")
    sandbox_workspace: str = Field(default="/var/exec-team-workspace", alias="SANDBOX_WORKSPACE")
    sandbox_timeout_seconds: int = Field(default=3600, alias="SANDBOX_TIMEOUT_SECONDS")
    sandbox_claude_code_max_turns: int = Field(default=50, alias="SANDBOX_CLAUDE_CODE_MAX_TURNS")
    sandbox_claude_model: str = Field(default="claude-sonnet-4-6", alias="SANDBOX_CLAUDE_MODEL")

    # Toggles
    nl_router_enabled: bool = Field(default=True, alias="NL_ROUTER_ENABLED")
    reflection_enabled: bool = Field(default=True, alias="REFLECTION_ENABLED")
    researcher_auto_scan: bool = Field(default=False, alias="RESEARCHER_AUTO_SCAN")
    curator_auto_run: bool = Field(default=False, alias="CURATOR_AUTO_RUN")

    # Thread Engine
    thread_default_max_rounds: int = Field(default=3, alias="THREAD_DEFAULT_MAX_ROUNDS")
    thread_default_max_messages: int = Field(default=8, alias="THREAD_DEFAULT_MAX_MESSAGES")
    thread_deep_max_rounds: int = Field(default=5, alias="THREAD_DEEP_MAX_ROUNDS")
    thread_deep_max_messages: int = Field(default=15, alias="THREAD_DEEP_MAX_MESSAGES")

    # Codebase
    codebase_snapshot_dir: str = Field(default="/var/exec-team-codebase-snapshot", alias="CODEBASE_SNAPSHOT_DIR")
    codebase_refresh_hours: int = Field(default=6, alias="CODEBASE_REFRESH_HOURS")

    # Skills
    skills_enabled: bool = Field(default=True, alias="SKILLS_ENABLED")
    skills_dir: str = Field(default="/app/skills", alias="SKILLS_DIR")

    @field_validator(
        "tg_topic_briefing", "tg_topic_decisions", "tg_topic_research",
        "tg_topic_strategy", "tg_topic_design", "tg_topic_engineering",
        "tg_topic_skills", "tg_topic_general",
        mode="before",
    )
    @classmethod
    def _empty_topic_to_zero(cls, v):
        if v is None or (isinstance(v, str) and v.strip() == ""):
            return 0
        return v

    @property
    def allowed_user_ids(self) -> set[int]:
        if not self.tg_allowed_users:
            return set()
        return {int(x.strip()) for x in self.tg_allowed_users.split(",") if x.strip()}


settings = Settings()
