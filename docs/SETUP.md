# CEO Setup Guide — executive-ai-team v3

> Полный шаг-за-шагом от чистой VM до работающей команды агентов.

## 0. Prerequisites

- Yandex Cloud VM, Ubuntu 22.04 LTS, минимум 4 vCPU / 8 GB RAM / 60 GB SSD
- Открыт SSH доступ
- Домен (опционально, для прокси/Cloudflare)

## 1. Создать 5 Telegram-ботов

Через @BotFather — 5 отдельных ботов:
- `<your_prefix>_chief_bot` — Chief of Staff
- `<your_prefix>_designer_bot` — Designer
- `<your_prefix>_cto_bot` — CTO
- `<your_prefix>_dev_bot` — Dev (общий для backend/frontend)
- `<your_prefix>_research_bot` — Research (Researcher + Strategist + Curator)

Каждому боту: `/setprivacy` → Disable (чтобы видел все сообщения в группе).

## 2. Создать супергруппу с топиками

В Telegram: Создать группу → конвертировать в Supergroup → включить Topics.

Создать 8 топиков:
- 📋 Briefing
- ⚖️ Decisions
- 🔬 Research
- 🎯 Strategy
- 🎨 Design
- 🔧 Engineering
- 🧠 Skills
- 💬 General

Пригласить всех 5 ботов в группу, дать им admin (для постинга в топики).

В каждом топике написать `/chatid` любым ботом — получишь thread_id (это и есть `TG_TOPIC_*`).

В General `/chatid` → `chat_id` (это `TG_GROUP_ID`).
Также узнай свой user_id (через @userinfobot) — это `TG_ALLOWED_USERS`.

## 3. Получить ключи

- Anthropic API key: console.anthropic.com → API keys
- GitHub PAT (classic) с правами `repo`, `read:org`, `workflow`: github.com/settings/tokens

## 4. Bootstrap VM

```bash
ssh user@<vm-ip>
curl -fsSL https://raw.githubusercontent.com/<you>/exec-team/main/scripts/setup-vm.sh | bash
newgrp docker
git clone https://github.com/<you>/exec-team.git ~/exec-team
cd ~/exec-team
cp .env.example .env
# Заполни .env (см. шаги выше)
nano .env
./scripts/check-env.sh
```

## 5. Собрать sandbox-образ

```bash
./scripts/build-sandbox-image.sh
```

(Образ будет ~1.5 GB, сборка ~5 минут.)

## 6. Snapshot существующего кода продукта

```bash
./scripts/refresh-codebase-snapshot.sh
```

Добавь в cron (для авто-обновления):
```bash
crontab -e
# добавь:
0 */6 * * * /home/$USER/exec-team/scripts/refresh-codebase-snapshot.sh >> /var/log/exec-team-snapshot.log 2>&1
```

## 7. Запустить команду

```bash
docker compose up -d --build
docker compose logs -f bot
```

В логах должны увидеть `Starting 5 bots in parallel`.

## 8. Smoke test

В Telegram любому из ботов:
- `/ping` — должен ответить «pong from <bot>»
- `/budget` — должен показать $0.00 / $150.00
- `/briefing` — Chief сформирует daily briefing
- `/context show project` — покажет PROJECT.md
- `/skills pending` — пусто пока

Если всё работает — поздравляю, команда онлайн.

## 9. Первая фича

В chief-боте:
```
/feature Добавить кнопку shareResult на экран результатов скана
```

Команда подхватит, Chief начнёт уточнение, потом Designer сделает мокап, CTO нарежет таски, dev-агенты откроют PR'ы. Ты получишь нотификации в соответствующие топики.
