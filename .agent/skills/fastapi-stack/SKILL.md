---
name: fastapi-stack
description: FastAPI + SQLAlchemy 2 async + Alembic + ARQ + uvicorn conventions.
---

# FastAPI stack

| Piece      | Path / tool                            |
| ---------- | -------------------------------------- |
| API        | `apps/api/app/main.py`                 |
| Routers    | `app/routers/` — thin                  |
| Services   | `app/services/` — all writes           |
| Models     | `app/models/`                          |
| Migrations | Alembic `migrations/`                  |
| Worker     | ARQ `app/workers/`                     |
| Config     | Pydantic Settings `app/core/config.py` |

Run: `pnpm run dev:api`, `pnpm run dev:worker`. Local DB via `pnpm run dev:docker`.
