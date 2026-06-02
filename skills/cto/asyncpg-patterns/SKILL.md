# asyncpg patterns for moy-kosmetolog backend

## When to apply
You're нарезаете tasks for `backend_dev` and the task touches database access.

## Rules
- Project uses **asyncpg directly**, NOT SQLAlchemy ORM.
- Acquire connections via context manager:
  ```python
  async with pool.acquire() as c:
      row = await c.fetchrow("SELECT ... WHERE id=$1", arg)
  ```
- Use `fetchrow` for single row, `fetch` for many, `execute` for write.
- Always parameterize: `$1, $2` — never f-string interpolation.
- Migrations through Alembic with `op.execute("CREATE TABLE ...")`.

## Money fields
Store as **integer kopecks** (e.g. 12999 = 129.99₽). Never float, never Decimal. Convert at API boundary.

## Pass to dev agent
Include in TASK.md → "Rules":
- Use `pool.acquire()` context manager, no manual conn handling
- Money as integer kopecks
- New tables via Alembic migration in `alembic/versions/`
