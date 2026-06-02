"""Anthropic API wrapper with retry, timeout, prompt caching, tool-use loop."""
from __future__ import annotations
import asyncio
import time
from typing import Any, Callable, Awaitable
from uuid import UUID
import httpx
from anthropic import AsyncAnthropic
from anthropic.types import Message
from loguru import logger

from core.config import settings
from core.exceptions import AgenticIterationLimitReached


# Цены на токены (центы за 1M)
# Источник: console.anthropic.com (на 2026-06)
PRICING_CENTS_PER_1M = {
    "claude-opus-4-7":   {"input": 1500, "output": 7500, "cache_write": 1875, "cache_read": 150},
    "claude-sonnet-4-6": {"input": 300,  "output": 1500, "cache_write": 375,  "cache_read": 30},
    "claude-haiku-4-5":  {"input": 80,   "output": 400,  "cache_write": 100,  "cache_read": 8},
}


def _calculate_cost_cents(model: str, usage) -> float:
    """Считает стоимость в центах с учётом кеша."""
    p = PRICING_CENTS_PER_1M.get(model)
    if not p:
        logger.warning("Unknown pricing for model {}, using sonnet defaults", model)
        p = PRICING_CENTS_PER_1M["claude-sonnet-4-6"]
    cost = 0.0
    cost += (usage.input_tokens / 1_000_000) * p["input"]
    cost += (usage.output_tokens / 1_000_000) * p["output"]
    cache_creation = getattr(usage, "cache_creation_input_tokens", 0) or 0
    cache_read = getattr(usage, "cache_read_input_tokens", 0) or 0
    cost += (cache_creation / 1_000_000) * p["cache_write"]
    cost += (cache_read / 1_000_000) * p["cache_read"]
    return cost


def _make_client() -> AsyncAnthropic:
    """Создаёт клиент с прокси если задан."""
    http_client_kwargs = {
        "timeout": httpx.Timeout(settings.anthropic_timeout_seconds, connect=15.0),
    }
    if settings.anthropic_proxy_url:
        http_client_kwargs["proxies"] = settings.anthropic_proxy_url
    return AsyncAnthropic(
        api_key=settings.anthropic_api_key,
        http_client=httpx.AsyncClient(**http_client_kwargs),
        max_retries=0,  # делаем retry сами
    )


_client: AsyncAnthropic | None = None


def get_client() -> AsyncAnthropic:
    global _client
    if _client is None:
        _client = _make_client()
    return _client


def _apply_prompt_cache(system: list[dict] | str) -> list[dict]:
    """Конвертирует system в list-формат с cache_control на последнем блоке."""
    if isinstance(system, str):
        blocks = [{"type": "text", "text": system}]
    else:
        blocks = list(system)
    if settings.prompt_cache_enabled and blocks:
        # cache_control на последнем text-блоке системника
        last = blocks[-1]
        if last.get("type") == "text":
            blocks[-1] = {**last, "cache_control": {"type": "ephemeral"}}
    return blocks


async def call_llm(
    *,
    model: str,
    system: str | list[dict],
    messages: list[dict[str, Any]],
    max_tokens: int = 4000,
    tools: list[dict] | None = None,
    pool=None,
    agent_role: str | None = None,
    feature_id: UUID | None = None,
    task_id: UUID | None = None,
    thread_id: UUID | None = None,
    operation_kind: str = "one_shot",
) -> dict[str, Any]:
    """
    Single LLM call с retry и логированием. Возвращает dict:
        {"content": str, "usage": {...}, "stop_reason": str, "raw": Message, "error": None}
    На ошибке: {"content": "", "error": str, ...}
    """
    client = get_client()
    system_blocks = _apply_prompt_cache(system)
    started = time.time()

    last_error: Exception | None = None
    resp: Message | None = None
    for attempt in range(settings.anthropic_max_retries + 1):
        try:
            kwargs = dict(
                model=model,
                max_tokens=max_tokens,
                system=system_blocks,
                messages=messages,
            )
            if tools:
                kwargs["tools"] = tools
            resp = await client.messages.create(**kwargs)
            last_error = None
            break
        except Exception as e:
            last_error = e
            wait = 2 ** attempt
            logger.warning("Anthropic call failed (attempt {}): {}. Retrying in {}s.", attempt + 1, e, wait)
            if attempt < settings.anthropic_max_retries:
                await asyncio.sleep(wait)

    duration_ms = int((time.time() - started) * 1000)

    if resp is None:
        # все попытки провалились
        if pool and agent_role:
            await _log_call(
                pool, agent_role=agent_role, model=model,
                in_tok=0, out_tok=0, cache_creation=0, cache_read=0,
                cost_cents=0.0, duration_ms=duration_ms, iterations=1,
                success=False, error=str(last_error),
                feature_id=feature_id, task_id=task_id, thread_id=thread_id,
                operation_kind=operation_kind,
            )
        return {"content": "", "error": str(last_error), "stop_reason": "error", "usage": None, "raw": None}

    in_tok = resp.usage.input_tokens
    out_tok = resp.usage.output_tokens
    cache_creation = getattr(resp.usage, "cache_creation_input_tokens", 0) or 0
    cache_read = getattr(resp.usage, "cache_read_input_tokens", 0) or 0
    cost_cents = _calculate_cost_cents(model, resp.usage)

    text_out = "".join(
        b.text for b in resp.content if getattr(b, "type", None) == "text"
    )

    if pool and agent_role:
        await _log_call(
            pool, agent_role=agent_role, model=model,
            in_tok=in_tok, out_tok=out_tok,
            cache_creation=cache_creation, cache_read=cache_read,
            cost_cents=cost_cents, duration_ms=duration_ms, iterations=1,
            success=True, error=None,
            feature_id=feature_id, task_id=task_id, thread_id=thread_id,
            operation_kind=operation_kind,
        )

    return {
        "content": text_out,
        "usage": {
            "input_tokens": in_tok, "output_tokens": out_tok,
            "cache_creation": cache_creation, "cache_read": cache_read,
            "cost_cents": cost_cents,
        },
        "stop_reason": resp.stop_reason,
        "raw": resp,
        "error": None,
    }


async def agentic_loop(
    *,
    model: str,
    system: str | list[dict],
    messages: list[dict[str, Any]],
    tools: list[dict],
    tool_executor: Callable[[str, dict], Awaitable[str]],
    max_iterations: int,
    max_tokens: int = 4000,
    pool=None,
    agent_role: str | None = None,
    feature_id: UUID | None = None,
    task_id: UUID | None = None,
    thread_id: UUID | None = None,
) -> dict[str, Any]:
    """
    Tool-use loop. Зацикливается пока Claude не отдаст stop_reason != 'tool_use' или не достигнет max_iterations.

    Возвращает то же что call_llm, плюс ключи:
        "iterations": int
        "tool_calls_log": list[{"tool": str, "input": dict, "result": str}]
    """
    client = get_client()
    system_blocks = _apply_prompt_cache(system)
    current_messages = list(messages)
    iterations = 0
    total_in = total_out = total_cache_create = total_cache_read = 0
    total_cost = 0.0
    final_text_parts: list[str] = []
    tool_calls_log: list[dict] = []
    started = time.time()
    last_error: str | None = None
    last_stop_reason: str = "max_iterations_reached"

    while iterations < max_iterations:
        iterations += 1
        resp = None
        last_error_iter: Exception | None = None
        for attempt in range(settings.anthropic_max_retries + 1):
            try:
                resp = await client.messages.create(
                    model=model,
                    max_tokens=max_tokens,
                    system=system_blocks,
                    messages=current_messages,
                    tools=tools,
                )
                last_error_iter = None
                break
            except Exception as e:
                last_error_iter = e
                if attempt < settings.anthropic_max_retries:
                    await asyncio.sleep(2 ** attempt)

        if resp is None:
            last_error = str(last_error_iter)
            logger.error("Agentic loop iter={} all retries failed: {}", iterations, last_error)
            break

        total_in += resp.usage.input_tokens
        total_out += resp.usage.output_tokens
        cc = getattr(resp.usage, "cache_creation_input_tokens", 0) or 0
        cr = getattr(resp.usage, "cache_read_input_tokens", 0) or 0
        total_cache_create += cc
        total_cache_read += cr
        total_cost += _calculate_cost_cents(model, resp.usage)

        # собираем текст + tool_uses
        tool_uses = []
        for block in resp.content:
            if getattr(block, "type", None) == "text":
                final_text_parts.append(block.text)
            elif getattr(block, "type", None) == "tool_use":
                tool_uses.append(block)

        last_stop_reason = resp.stop_reason

        if resp.stop_reason != "tool_use" or not tool_uses:
            # финал
            break

        # добавляем assistant message с tool_uses в историю
        current_messages.append({"role": "assistant", "content": resp.content})

        # выполняем tools
        tool_results = []
        for tu in tool_uses:
            try:
                result = await tool_executor(tu.name, tu.input)
            except Exception as e:
                logger.exception("Tool {} execution failed", tu.name)
                result = f"Error executing tool: {e}"
            tool_calls_log.append({"tool": tu.name, "input": tu.input, "result": result[:500]})
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": tu.id,
                "content": result,
            })

        # отвечаем результатами как user message
        current_messages.append({"role": "user", "content": tool_results})

    duration_ms = int((time.time() - started) * 1000)
    final_text = "\n".join(p for p in final_text_parts if p)

    if iterations >= max_iterations and last_stop_reason == "tool_use":
        last_error = f"Reached max_iterations={max_iterations} without final answer"
        logger.warning("Agentic loop exhausted for {}: {}", agent_role, last_error)

    if pool and agent_role:
        await _log_call(
            pool, agent_role=agent_role, model=model,
            in_tok=total_in, out_tok=total_out,
            cache_creation=total_cache_create, cache_read=total_cache_read,
            cost_cents=total_cost, duration_ms=duration_ms, iterations=iterations,
            success=(last_error is None), error=last_error,
            feature_id=feature_id, task_id=task_id, thread_id=thread_id,
            operation_kind="agentic",
        )

    return {
        "content": final_text,
        "iterations": iterations,
        "tool_calls_log": tool_calls_log,
        "stop_reason": last_stop_reason,
        "usage": {
            "input_tokens": total_in, "output_tokens": total_out,
            "cache_creation": total_cache_create, "cache_read": total_cache_read,
            "cost_cents": total_cost,
        },
        "error": last_error,
    }


async def _log_call(
    pool, *, agent_role: str, model: str,
    in_tok: int, out_tok: int, cache_creation: int, cache_read: int,
    cost_cents: float, duration_ms: int, iterations: int,
    success: bool, error: str | None,
    feature_id, task_id, thread_id, operation_kind: str,
) -> None:
    try:
        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO agent_calls
                    (feature_id, task_id, thread_id, agent_role, model,
                     input_tokens, output_tokens, cache_creation_tokens, cache_read_tokens,
                     cost_cents, duration_ms, iterations, success, error, operation_kind)
                VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15)
                """,
                feature_id, task_id, thread_id, agent_role, model,
                in_tok, out_tok, cache_creation, cache_read,
                cost_cents, duration_ms, iterations, success, error, operation_kind,
            )
    except Exception as e:
        logger.warning("Failed to log agent call: {}", e)
