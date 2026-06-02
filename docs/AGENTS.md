# Agents — executive-ai-team v3

## Chief of Staff (Opus 4.7)
**Bot:** chief
**Mode:** agentic (max 5 iterations)
**Tools:** memory, threads, ask_agent
**Role:** второй мозг CEO, оркестрация, daily briefing, thread summarization → ceo_pending_decisions

## Designer (Opus 4.7)
**Bot:** designer
**Mode:** agentic (max 20 iterations)
**Tools:** memory, threads, ask_agent, codebase (read-only)
**Role:** мокапы (HTML+Tailwind через playwright → PNG), EDIT/NEW modes, partner in design thinking
**НЕ делает:** не запускает dev server, не пишет production код

## CTO Tasking (Opus 4.7)
**Bot:** cto
**Mode:** agentic (max 20 iterations)
**Tools:** memory, threads, ask_agent, codebase (read-only)
**Role:** разбивка approved-мокапа на executable spec'ы с готовым планом (affected_files + changes_per_file + acceptance + api_contract)

## CTO Review (Opus 4.7)
**Bot:** cto
**Mode:** agentic (max 20 iterations)
**Tools:** memory, threads, codebase (read-only), GitHub PR diff
**Role:** PR review: approve / request_changes с конкретными комментариями

## Researcher (Opus 4.7)
**Bot:** research
**Mode:** agentic (max 20 iterations)
**Tools:** memory, threads, ask_agent, web_search (Anthropic native)
**Role:** ресерч конкурентов, рынка, валидация гипотез. Записывает в research_findings.

## Strategist (Opus 4.7)
**Bot:** research
**Mode:** agentic (max 20 iterations)
**Tools:** memory, threads, ask_agent
**Role:** гипотезы в формате (гипотеза/основание/эксперимент/метрика/срок), приоритизация под North Star

## Skill Curator (Opus 4.7)
**Bot:** research
**Mode:** agentic (max 10 iterations) или weekly cron
**Tools:** memory, ask_agent
**Role:** анализ reflections + signals, max 3 proposals/week, CEO approve → SKILL.md

## Dev agents (Sonnet 4.6 или Haiku 4.5)
**Bot:** dev
**Mode:** Claude Code в Docker sandbox (max 50 turns)
**Tools:** Claude Code native (file system, bash, etc — внутри sandbox)
**Role:** реализация конкретного таска от CTO → PR в продуктовый репо

## NL Router (Sonnet 4.6)
**Bot:** any (fallback handler)
**Mode:** one-shot
**Role:** классификация intent + target_agent для свободного текста
