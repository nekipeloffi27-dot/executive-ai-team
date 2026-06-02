# Tech stack — moy-kosmetolog

## Repo structure (monorepo)

pnpm workspaces. На корне `package.json`, `docker-compose.yml`, `init.sql`, `nginx/`, `nginx.conf`.

```
moy-kosmetolog/
├── packages/
│   ├── api-python/    # FastAPI backend (главный бэк)
│   ├── web/           # Next.js 16 PWA
│   └── api/           # legacy Node/Fastify (ignore)
├── docker-compose.yml
├── init.sql
└── nginx/, nginx.conf
```

External repo: `../moy-kosmetolog-admin` — admin CMS (mounted in Docker как `kosmetolog-admin`).

**Where агенты работают:**
- `backend_dev` → `packages/api-python/`
- `frontend_web_dev` → `packages/web/`
- `frontend_mobile_dev` → Phase 2, ещё не создан

## Backend (packages/api-python)

- Python 3.12, FastAPI
- **SQLAlchemy 2.0 async ORM** (НЕ raw asyncpg — существующий код через ORM)
- Alembic для миграций (`packages/api-python/migrations/`)
- Pydantic 2.x для request/response
- Auth: JWT access (15 min) + refresh (30 days), OTP через SMS.ru (mocked в dev)
- OAuth: Apple / Google / VK / Yandex / Telegram
- AI: OpenAI GPT-4o (`OPENAI_VISION_MODEL=gpt-4o`) для skin scan + Anthropic Claude (`claude-sonnet-4-5`) для chat/recs
- Storage: Yandex Cloud S3 (boto3)
- DB: PostgreSQL 16, Redis 7

**Roots:** API base `/api/v1`, app factory `app/main.py`, dev порт 3000.

**Routers (13 модулей):** `/auth /profile /scan /home /articles /cosmetic_analysis /recommendations /diary /feed /chat /doctors /upload /routine`

**Models:** User, Scan, SkinDiaryEntry, FeedPost, Comment, Like, Recommendation, ChatSession, ChatMessage, DoctorProfile, DoctorReview, UserRoutine, RoutineProduct, Article

## Frontend Web (packages/web)

- **Next.js 16** App Router (port 3001 в dev)
- **React 19**, TypeScript strict
- **Tailwind CSS v4** + **Halo DS** (custom design system в `packages/web/halo-ds/`)
- TanStack Query v5 (server state)
- Zustand v5 (client state)
- axios (HTTP client с JWT-interceptor)
- react-hook-form + zod (forms)
- PWA: service worker в `app/layout.tsx`, `manifest.json`
- MediaPipe client-side для skin landmark detection до upload скана

### Halo DS quick rules
- Tokens в `packages/web/halo-ds/tokens.css`
- 4 темы: cream (default) / rose / sage / midnight
- Шрифты: Inter (body), Instrument Serif (display), JetBrains Mono (code)
- Components: HaloGlass, HaloButton, HaloRing, HaloTabBar, HaloSheet, HaloHeading
- Полная документация: `packages/web/halo-ds/CLAUDE.md`

## Admin CMS (внешний репо ../moy-kosmetolog-admin)

Next.js, mounted как `kosmetolog-admin` сервис в docker-compose. Port 3002. Не в фокусе exec-team пока.

## Phase 2 mobile (packages/mobile)

Ещё не создан. Стек: Kotlin 2.x, KMP, Compose Multiplatform, Ktor client, SQLDelight. Halo DS портирован на Compose позже.

## Infrastructure

- VM в Yandex Cloud (РФ-юрисдикция критична)
- PostgreSQL 16, Redis 7
- nginx reverse-proxy: `/api/*` → FastAPI :3000, `/admin` → CMS :3002, `/` → PWA :3001
- Yandex Object Storage (S3-совместимое) для фото пользователей
- GitHub Actions для CI

## Inviolable invariants

1. **Never hard-delete** — soft-delete через `deleted_at TIMESTAMPTZ`
2. PII (phone, email, photo URLs) не в INFO-логах, только DEBUG
3. Datetimes как `TIMESTAMPTZ` UTC, конвертация на границе
4. Phone в E.164: `+7XXXXXXXXXX`
5. Anonymous flows: `anonymous_token` (в localStorage у PWA) обязателен для unauth endpoints

## Banned dependencies

- shadcn/ui, Material UI (используем Halo DS)
- Django (FastAPI выбор)
- Raw asyncpg в новом коде backend'а (используем SQLAlchemy ORM как в существующем)
- Любые третьи аналитики без явного user consent

## Naming conventions

- Python: snake_case, файлы snake_case, классы CamelCase
- TS: camelCase, PascalCase для компонентов и типов, kebab-case для файлов
- Git branches: `feat/<slug>-<task_id_8>`, `fix/<slug>-<task_id_8>`
- Commits: Conventional Commits (`feat:`, `fix:`, `chore:`, `docs:`, `refactor:`)

## Tone / voice

Russian, обращение **"ты"**. Тёплый, экспертный, не corporate. См. `DESIGN_SYSTEM.md`.
