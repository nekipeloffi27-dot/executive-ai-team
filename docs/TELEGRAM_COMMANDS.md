# Telegram commands cheat sheet

## Базовое (любой бот)
- `/start` — приветствие
- `/ping` — проверка живости
- `/chatid` — узнать chat_id, user_id, thread_id (для setup)
- `/version`

## Фичи (chief bot)
- `/feature <описание>` — создать новую фичу
- `/status [feature_id]` — статус одной или всех активных фич
- `/cancel <feature_id>` — отменить (убивает sandbox если запущен)
- `/unblock <feature_id> [new_state]` — снять blocked
- `/retry <feature_id>` — перезапустить последнюю упавшую таску

## Контекст (chief bot)
- `/context list` — список context-файлов
- `/context show <alias>` — показать (alias: project, goal, competitors, tech_stack, design_system, moodboard, anti_references)
- `/context edit <alias>` — путь на VM для редактирования (hot-reload по mtime)

## Бюджет (chief bot)
- `/budget` — месячный cap, потрачено, by-agent breakdown
- `/cost` — last 24h и last 7d

## Обсуждения (chief bot)
- `/discuss [deep] @mention @mention тема вопроса` — открыть thread с участниками и провести max_rounds раундов
  - Доступные mentions: `@chief @designer @cto @researcher @strategist`
  - `deep` режим: 5 раундов / 15 сообщений / $3 вместо default 3/8/$1
- `/threads` — активные threads
- `/decision <thread_id_prefix> <выбор>` — зафиксировать решение по thread'у (сохранит в decisions)

## Ресерч (chief bot)
- `/research <тема>` — Researcher делает on-demand ресерч → сохранит в research_findings

## Скиллы (chief bot)
- `/skills pending` — proposals на approve
- `/skills run` — запустить Curator вручную
- `/skill_approve <id>` — записать SKILL.md
- `/skill_reject <id>`
- `/skill_disable <name>` — выключить approved skill

## Briefing (chief bot)
- `/briefing` — daily summary от Chief of Staff
