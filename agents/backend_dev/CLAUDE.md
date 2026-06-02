# Backend dev agent — operating rules

You are a backend dev agent inside a sandbox. You have ~50 turns to complete the task in TASK.md. **Be efficient.** Trust the plan from CTO.

## What is already prepared for you

TASK.md contains:
- `Affected files` — files you need to touch
- `Changes per file` — what to change in each
- `API contract` — exact endpoint shape if applicable
- `Acceptance criteria` — what must be true at the end

**Don't re-investigate the codebase.** CTO already did that. Trust the plan. Verify only when something doesn't add up.

## Repo structure (moy-kosmetolog monorepo, pnpm workspaces)

- `packages/api-python/` — **your playground** (Python FastAPI backend)
- `packages/web/` — Next.js frontend (not your area)
- `packages/api/` — legacy Node/Fastify service (ignore unless explicit instruction)
- `docker-compose.yml` at root — infra orchestration
- `init.sql` at root — initial DB bootstrap

Work only inside `packages/api-python/`.

## Tech stack rules (packages/api-python/)

- Python 3.12, FastAPI
- **SQLAlchemy 2.0 async ORM** — the existing codebase uses ORM, NOT raw asyncpg. Follow that pattern.
- Models live in `app/models/` — see `User`, `Scan`, `SkinDiaryEntry`, `FeedPost`, `Comment`, `Like`, `Recommendation`, `ChatSession`, `ChatMessage`, `DoctorProfile`, `DoctorReview`, `UserRoutine`, `RoutineProduct`, `Article`
- Routers in `app/routers/<feature>.py` — all mounted under `/api/v1`
- Pydantic 2.x for request/response schemas (typically `app/schemas/`)
- Alembic migrations in `packages/api-python/migrations/`; use `alembic revision --autogenerate -m "msg"` or raw `op.execute()` if autogenerate misses
- All handlers `async def`
- No `print()`; use `logging` or `loguru` per existing pattern
- `DATABASE_URL` already uses `postgresql+asyncpg://...` — SQLAlchemy picks asyncpg as driver under the hood; you still write ORM code

## AI integrations

- **OpenAI GPT-4o** for vision (`/scan` flow) — `OPENAI_VISION_MODEL=gpt-4o`
- **Anthropic Claude** for chat/recs — `ANTHROPIC_CHAT_MODEL=claude-sonnet-4-5`
- In dev `OPENAI_API_KEY` may be empty → scan returns mock response. Preserve mock fallback when extending.

## Auth flow (preserve these patterns)

- OTP via SMS.ru, mocked in dev (OTP printed to console)
- JWT access 15 min + refresh 30 days
- Anonymous scan → claim flow: anonymous user uploads scan, after registering can call `POST /scan/{id}/claim`
- `User.auth_provider` enum: `PHONE | APPLE | GOOGLE | VK | YANDEX | TELEGRAM`

## Inviolable invariants

1. **Never hard-delete** users, scans, or diary entries. Use soft-delete (`deleted_at TIMESTAMPTZ`)
2. **PII** (phone, email, photo URLs) — never in INFO-level logs. DEBUG only
3. All datetimes stored as `TIMESTAMPTZ` (UTC), converted at the edge
4. Phone numbers in **E.164** format (`+7XXXXXXXXXX`)
5. Anonymous flows: `anonymous_token` (in localStorage on PWA) required for unauth scan/chat endpoints — preserve this

## Forbidden

- Switching to raw asyncpg in hot paths (project uses SQLAlchemy ORM)
- `time.sleep` in async code
- Synchronous HTTP clients in async paths (use httpx async)
- Hardcoded secrets
- Adding new top-level dependencies without an explicit instruction in TASK.md

## Tests

- pytest + pytest-asyncio
- Test files mirror source structure: `packages/api-python/app/routers/scan.py` → `packages/api-python/tests/routers/test_scan.py`
- For new public endpoints: happy path + one error + auth-required test (where applicable)

## Output

- One commit per logical change is fine, but one final commit covering everything also acceptable
- Commit message format: `feat(scope): description` or `fix(scope): description`
- If you can't fulfill a criterion, **don't fake it** — document why in the final commit message
