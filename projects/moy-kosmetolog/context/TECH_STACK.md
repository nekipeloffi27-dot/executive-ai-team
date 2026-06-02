# Tech stack — moy-kosmetolog

## Repo structure (monorepo)

pnpm workspaces. На корне `package.json`, `docker-compose.yml`, `init.sql`, `nginx.conf`.

```
moy-kosmetolog/
├── packages/
│   ├── web/           # Next.js 14 frontend (PWA)
│   ├── api-python/    # FastAPI backend (главный бэк)
│   └── api/           # вспомогательный Node.js сервис
├── docker-compose.yml # инфра для локальной разработки
├── init.sql           # начальная схема БД
└── nginx/, nginx.conf # reverse-proxy
```

При работе с кодом продукта:
- **Frontend задачи** → `packages/web/`
- **Backend (Python) задачи** → `packages/api-python/`
- **Node-сервис** → `packages/api/` (не основной фокус сейчас)

## Backend
- Python 3.12
- FastAPI 0.115+
- asyncpg (raw SQL — НЕ SQLAlchemy ORM)
- Alembic для миграций (raw SQL через op.execute)
- Pydantic 2.x
- Auth: JWT, refresh tokens в Redis
- Background tasks: Dramatiq + Redis
- Object storage: Yandex Object Storage (S3-совместимое) через boto3-async

## Frontend Web
- Next.js 14 App Router
- React 18, TypeScript strict mode
- Tailwind CSS + Halo Design System tokens
- TanStack Query для server state
- Zustand для client state
- react-hook-form + zod
- API client автогенерится из OpenAPI

## Halo Design System
- Tokens: spacing, color, radius, typography — см. `web/lib/halo/`
- Components: Button, Input, Card, ResultCard, etc — см. `web/components/halo/`
- Шрифты: Halo Display (заголовки), Halo Text (тело)

## Phase 2 mobile
- Kotlin 2.x, Kotlin Multiplatform Mobile
- Compose Multiplatform для UI
- Ktor client
- SQLDelight для локального хранилища
- Shared module: бизнес-логика, API client, models

## Infrastructure
- VM в Yandex Cloud (РФ-юрисдикция критична)
- PostgreSQL 15
- Redis 7
- Cloudflare (proxy и DDoS защита)
- GitHub Actions для CI

## Banned dependencies
- SQLAlchemy ORM (используем asyncpg напрямую)
- Django (FastAPI выбор)
- Material UI (используем Halo DS)
- Любые библиотеки требующие лицензии для коммерческого использования без явной оплаты

## Naming conventions
- Python: snake_case, файлы snake_case, классы CamelCase
- TS: camelCase для переменных/функций, PascalCase для компонентов и типов, kebab-case для файлов компонентов
- Git branches: `feat/<slug>-<task_id_8>`, `fix/<slug>-<task_id_8>`
- Commit messages: Conventional Commits (`feat:`, `fix:`, `chore:`, `docs:`, `refactor:`)
