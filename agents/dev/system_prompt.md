# Dev Agent (orchestrator runner)

Это **не** промпт для LLM. Это инструкция для оркестратора, который spawns sandbox.

Dev-агент работает в Docker sandbox через Claude Code (см. `agents/dev/sandbox/`). Реальный промпт для Claude Code в sandbox составляется в runtime из:

1. `agents/<dev_role>/CLAUDE.md` — контекст продукта (монтируется в sandbox)
2. `agents/<dev_role>/role_prompt.md` — role-specific rules
3. TASK.md — конкретный таск с готовым планом от CTO

Подробности в `agents/dev/runner.py` (Часть 5).
