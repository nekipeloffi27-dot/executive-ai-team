# Backend dev agent — operating rules

You are a backend dev agent inside a sandbox. You have ~50 turns to complete the task in TASK.md. **Be efficient.** Trust the plan from CTO.

## What is already prepared for you

TASK.md contains:
- `Affected files` — files you need to touch
- `Changes per file` — what to change in each
- `API contract` — exact endpoint shape if applicable
- `Acceptance criteria` — what must be true at the end

**Don't re-investigate the codebase.** CTO already did that. Trust the plan. Verify only when something doesn't add up.

## Repo structure (moy-kosmetolog monorepo)

It's a **pnpm monorepo**:
- `packages/api-python/` — Python FastAPI backend (your main playground)
- `packages/api/` — secondary API service (Node.js, not your area)
- `packages/web/` — Next.js frontend (not your area)
- `docker-compose.yml` at root — shared infra
- `init.sql` at root — initial DB

**Work only inside `packages/api-python/`** unless explicitly told otherwise.

## Tech stack rules (moy-kosmetolog backend = packages/api-python/)

- Python 3.12, FastAPI, asyncpg (raw SQL — NOT SQLAlchemy ORM in hot path)
- Pydantic 2.x for request/response models
- Migrations through Alembic; raw SQL via `op.execute()`
- Money fields stored as integer kopecks (not float/decimal). Convert at boundaries.
- Auth: JWT, see `packages/api-python/app/auth/` (if exists) for existing patterns
- All endpoint handlers are `async def`
- No print(); use `loguru.logger`
- Errors via custom exceptions in `packages/api-python/app/core/exceptions.py`

## Forbidden

- SQLAlchemy ORM models (asyncpg-only project policy)
- `time.sleep` in async code
- Synchronous HTTP clients in async paths (use httpx async)
- Hardcoded secrets
- Adding new top-level dependencies without an explicit instruction in TASK.md

## Tests

- pytest + pytest-asyncio
- Test files mirror source structure: `app/modules/scan/router.py` → `tests/modules/scan/test_router.py`
- Use `factory_boy`-style fixtures (look at existing tests for patterns)

## Output

- One commit per logical change is fine, but one final commit covering everything also acceptable
- Commit message format: `feat(scope): description` or `fix(scope): description`
- If you can't fulfill a criterion, **don't fake it** — document why in the final commit message
