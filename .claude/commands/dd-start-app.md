# dd-start-app

Start the local DoctorDesk stack.

```bash
pnpm run dev:docker   # if Postgres/Redis not up
pnpm run dev          # web + api + worker
```

Copy `apps/api/.env.example` → `apps/api/.env` on first run. Web: http://localhost:3100 · API: http://localhost:8100/docs. If ports are busy, run `pnpm run dev:free-ports` first (also runs automatically via `pnpm dev`).
