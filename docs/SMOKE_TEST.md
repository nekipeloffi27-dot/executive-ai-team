# Smoke test после первого деплоя

После того как `docker compose up -d --build` пройдёт и в логах появилось `Starting 5 bots in parallel` — прогони эту проверку.

## 1. Базовая живость (1 минута)
- Любому боту: `/ping` → должен ответить «pong from <name>»
- `/version` → `executive-ai-team v3 (<name>)`

## 2. БД и pre-seeded данные
- chief bot: `/context show project` — должен показать PROJECT.md
- chief bot: `/context show goal` — North Star + phased KPI
- chief bot: `/budget` — `Cap: $150.00, Spent: $0.00, ...`

## 3. Pre-seeded decisions
В БД должны быть 7 pre-seeded решений:
```bash
docker compose exec db psql -U exec_team -d exec_team -c "SELECT topic FROM decisions WHERE project_slug='moy-kosmetolog';"
```
Ожидаемо: 7 строк.

## 4. Pre-seeded pending decision (wall-auth)
chief bot: `/threads` — пока пусто  (pending decision не привязан к thread без обсуждения)

Проверка в БД:
```bash
docker compose exec db psql -U exec_team -d exec_team -c "SELECT title FROM ceo_pending_decisions WHERE decided=FALSE;"
```
Ожидаемо: 1 строка про wall-auth.

## 5. Briefing (первый живой agentic вызов)
chief bot: `/briefing` — Chief должен сформировать сводку. Должен использовать tools (read_decisions, read_recent_reflections, get_budget_status).

Это первое реальное списание бюджета.

После `/briefing`:
- `/cost` — last 24h должно показать ~$0.05-0.30

## 6. Research (one-shot agentic с web_search)
chief bot: `/research какие тренды в skincare apps на 2026 в РФ`

Researcher должен:
- Сделать 1-3 web_search вызовов
- Вернуть findings с URL-ями
- Сохранить в research_findings (проверь: `/context show project` не показывает, но `select * from research_findings limit 5;`)

## 7. Discussion (Thread Engine smoke)
chief bot: `/discuss @designer @cto Делаем quiz перед скрином сканера или сразу скан?`

Ожидаемо:
- Thread открыт
- 2-3 раунда участники друг другу отвечают
- Chief формирует summary с ceo_options A/B/C
- pending_decision создан

Затем: `/decision <thread_id_prefix> option_a` — фиксация.

## 8. Skill Curator (вручную)
chief bot: `/skills run`

С 5+ reflections/signals — может создать proposal. С 0 — вернёт 0.
После `/briefing` reflections нет (chief сам не пишет reflection в этом флоу) — пока 0.

## 9. Feature flow (требует прод-репо с настроенным GH доступом)
chief bot: `/feature Добавить кнопку Share на экран результатов скана`

Ожидаемо последовательность:
1. Chief уточняет (1-2 раунда), пишет в тред
2. Designer создаёт мокап (PNG) → постит в design топик
3. CEO approves (/approve_design <feature_id>) или дискачит
4. CTO нарезает таски (видишь JSON-таски в engineering топик)
5. Dev-агент в sandbox делает PR
6. CTO review постит approve / request_changes
7. CEO merge PR ручками

(Шаг 9 — это уже не smoke. Это первая боевая фича.)
