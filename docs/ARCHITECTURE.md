# Architecture — executive-ai-team v3

## High-level

CEO ↔ Telegram (5 bots) ↔ Bot Process (Python aiogram) ↔
  - Anthropic API (agentic agents with tool-use loops)
  - PostgreSQL (memory: decisions, threads, reflections, signals, costs)
  - Docker sandbox (dev agents running Claude Code with bounded turns)
  - GitHub API (PR review)

## Key design decisions

### 1. Настоящие agentic-агенты, не one-shot
Каждый агент (Designer, CTO, Researcher, Strategist, Chief, Curator) работает через **tool-use loop**. У него tools для чтения памяти, открытия threads, общения с другими агентами через `ask_agent`. Cap на итерации — 20 (Designer/CTO/Researcher/Strategist), 5 (Chief), 10 (Curator).

### 2. Real Thread Engine
Discussion threads — настоящий round-robin между участниками с жёсткими caps (default: 3 раунда / 8 сообщений / $1, deep: 5 / 15 / $3). После исчерпания Chief of Staff **обязан** сформулировать варианты A/B/C → автоматически создаёт `ceo_pending_decisions`.

### 3. Memory как 3 слоя
- **Structured**: `projects/<slug>/context/*.md` (PROJECT, GOAL, COMPETITORS, TECH_STACK, DESIGN_SYSTEM, MOODBOARD, ANTI_REFERENCES) + tables (decisions, roadmap, budget_caps)
- **Episodic**: agent_reflections (Haiku пост-фактум) + quality_signals (без LLM) + threads + research_findings
- **Working**: in-context messages в каждом вызове

Vector store (pgvector) отложен до 100+ reflections — пока не нужен.

### 4. Budget-aware
Critical agents (Designer, CTO, dev) **никогда** не блокируются бюджетом — иначе фича встанет. Non-critical (Researcher, Strategist, Curator, Reflection) блокируются при достижении hard_stop_pct (default 80% месячного cap'а).

### 5. Sandbox с фиксами v2
Docker-in-Docker для dev-агентов, но все боли v2 пре-фиксированы:
- Хост-путь = контейнер-путь (`/var/exec-team-workspace/<uuid>` = `/workspace`)
- UUID-суффиксы в именах контейнеров
- Прокси baked в Dockerfile (build-arg, не env)
- Транслитерация имён веток (никакой кириллицы)
- Timeout sandbox 3600s, API 900s, retry exp backoff
- Prompt caching включён
- Skills как `:ro` mount

### 6. Self-improvement loop
Reflections (Haiku) → quality_signals (без LLM) → Skill Curator (weekly, max 3 предложения) → CEO `/skill_approve` → SKILL.md в `skills/<role>/<name>/` → hot-mount к агенту.

## Plan B для sandbox (для справки, не реализован)
`claude-code-action` от Anthropic — GH Actions раннер вместо своего Docker. Можно мигрировать если боли v2 повторятся в v3. Не зашит сейчас потому что РФ-инфра-юрисдикция критична.

## File layout
См. `README.md` и структуру в Часть 0 промпта.

## Agents and their bots
- chief_of_staff → chief bot
- designer → designer bot
- cto_tasking, cto_review → cto bot
- dev_backend, dev_frontend_web, dev_frontend_mobile → dev bot
- researcher, strategist, skill_curator → research bot

## Models
- Thinking (Opus 4.7): chief_of_staff, designer, cto, researcher, strategist, skill_curator
- Working (Sonnet 4.6): NL router, sandbox dev (medium/complex tasks)
- Cheap (Haiku 4.5): sandbox dev (simple tasks)
- Reflection (Haiku 4.5): reflection tool
