# Phase 1: Monorepo scaffold, Docker Compose, auth, roles

**Status:** Done
**Depends on:** Phase 0
**Unlocks:** Phase 2

**mvp.md reference:** §13 item 1, §6.1, §6.11 · **tech-stack.md reference:** Monorepo, Frontend, Backend, Database, Local development

## Goal

Turn the empty repo (already has `package.json`, `turbo.json`, `pnpm-workspace.yaml`, `docker-compose.yml`, `CLAUDE.md`, and Cursor rules from Phase 0) into a running full-stack skeleton: `apps/web` boots a blank TanStack Start app, `apps/api` boots a FastAPI app with a health check, both talk to the Docker Compose Postgres/Redis, and a user can register/log in with JWT access+refresh tokens scoped to a clinic and a role. No product screens yet — this phase is pure foundation.

## Prerequisites

- Phase 0 complete (rules/skills in place so the agent building this phase follows `fastapi-conventions.mdc`, `tanstack-start-conventions.mdc`, `naming-conventions.mdc`, `migrations.mdc` from the start)
- Docker Desktop (or equivalent) running locally

## Tasks

### 1. Monorepo skeleton

- [ ] `apps/web/` — TanStack Start + Vite + TypeScript app, React 19
  - `src/routes/` (file-based routes, start with `__root.tsx`, `index.tsx`, `login.tsx`)
  - `src/features/` (empty, first feature folder lands in Phase 2 with `auth/`)
  - `src/lib/` — `apiClient.ts` stub (wires up the generated client from `packages/api-client` once it exists), `queryClient.ts`
  - `src/components/ui/` — shadcn/ui init
  - Tailwind CSS configured
  - `tsconfig.json` path alias `@/` → `apps/web/src/`
- [ ] `apps/api/` — FastAPI app
  - `app/main.py` — app factory, CORS, router mounting, exception handlers
  - `app/routers/` (empty except `health.py`)
  - `app/services/` (empty)
  - `app/models/` (empty except SQLAlchemy `Base` + `TimestampMixin`)
  - `app/schemas/` (empty)
  - `app/core/` — `config.py` (Pydantic Settings from env), `db.py` (async engine/session factory), `security.py` (JWT encode/decode, password hashing)
  - `app/workers/` (empty, ARQ worker entrypoint stub — real jobs start Phase 6/14)
  - `migrations/` — Alembic initialized, `env.py` wired to async engine + `Base.metadata`
  - `pyproject.toml` — uv-managed, ruff configured (lint + format), pytest configured
  - `.env.example`
- [ ] `packages/api-client/` — placeholder package.json + Orval config pointed at `apps/api`'s OpenAPI export path; generation wired but run manually until an endpoint exists to generate from
- [ ] `dev.sh` — orchestrates `docker compose up -d`, `apps/api` uvicorn, `apps/api` ARQ worker, `apps/web` vite dev, mirroring kame-homes' `dev.sh` shape but for this stack (no `--ui-only`/`--env dev` flags needed yet unless a hosted dev environment exists — add later if Phase 19 introduces one)
- [ ] `.vscode/tasks.json` — run tasks: "Dev: full stack" (`pnpm run dev`), "Dev: web only", "Dev: api only", "Dev: worker only", "DB: migrate", "DB: reset local", "Quality: ci gate", "Docker: up" / "Docker: down" — bind to the `package.json` scripts, not duplicate shell logic
- [ ] `.github/workflows/ci.yml` — type-check, lint, `check:filenames`, build, backend tests (pytest), frontend tests (Vitest); Playwright E2E as a separate slower job gated on `if: false` or a path filter until Phase 3+ has specs to run
- [ ] `.husky/pre-commit` — runs `lint-staged` (already configured in `package.json`)
- [ ] `apps/api/.env` local values documented in `apps/api/.env.example`; root `.env.example` if any root-level env vars are needed (none expected — Node tooling reads no secrets)

### 2. Scripts this phase owns (`scripts/dev/`, `scripts/deploy/`)

Fill in the `package.json` targets Phase 0 explicitly deferred:

- [ ] `scripts/dev/db-reset-local.sh` — drop + recreate local DB, `alembic upgrade head`, run seed
- [ ] `scripts/dev/env-status.sh` — print which `DATABASE_URL`/environment is currently active (dev/local/prod) by inspecting `apps/api/.env`
- [ ] `scripts/deploy/deploy-api.sh` — `dev`/`prod` args; `prod` path is a no-op stub that just prints "blocked, see no-prod-deploy.mdc" until Phase 19 wires a real target (Hetzner VPS not provisioned yet)
- [ ] `scripts/deploy/deploy-web.sh` — same shape, Cloudflare Pages target stubbed until Phase 19
- [ ] `scripts/deploy/migrate-remote.sh` — stubbed the same way (no remote Neon target provisioned yet)
- [ ] `scripts/deploy/backup-db.sh`, `scripts/deploy/rollback-db.sh` — stubbed; real implementation lands with Phase 19's deployment work once Neon/Hetzner exist

Stubbing these now (rather than leaving `package.json` scripts pointing at nonexistent files) keeps `pnpm run <script>` from hard-failing with "file not found" during early local dev, and gives Phase 19 a clear "replace stub with real logic" task instead of a blank slate.

### 3. Database foundations shared by every later phase

- [ ] `clinics` table — id, name, logo_url, address, contact info, timezone (default `Asia/Manila`), created_at/updated_at
- [ ] `users` table — id, email (unique), hashed_password, full_name, is_active, created_at/updated_at (no `clinic_id` here — see `clinic_memberships`)
- [ ] `clinic_memberships` table — user_id, clinic_id, role (`owner`/`admin`/`doctor`/`reception`), is_active, created_at (composite unique on user_id+clinic_id) — this is what makes multi-clinic-per-user and multi-doctor-per-clinic both possible without a redesign later
- [ ] `refresh_tokens` table — id, user_id, token_hash, expires_at, revoked_at, created_at (rotation-on-use, revocation on logout)
- [ ] `activity_log` table (append-only) — id, clinic_id, actor_user_id (nullable for system/AI actions), actor_type (`user`/`ai_assistant`/`system`), action, target_type, target_id, summary, metadata (jsonb), created_at. **Created in this phase even though nothing writes to it yet** — every later phase's service functions write here from day one, per `mvp.md` §6.11.
- [ ] Alembic: one migration per table above, reviewed (not blindly accepted from autogenerate)
- [ ] `btree_gist` extension enabled in this phase's migration (used starting Phase 5, enabling it early avoids a surprise migration dependency later)

### 4. Auth (`apps/api`)

- [ ] `POST /api/v1/auth/register` — creates a `users` row + first `clinics` row + `clinic_memberships` row with role `owner` (this is how a brand-new clinic is born — the onboarding wizard in Phase 3 takes over from here, this endpoint just gets the account and clinic shell to exist)
- [ ] `POST /api/v1/auth/login` — email+password, returns access token (short-lived, e.g. 15 min) + refresh token (long-lived, e.g. 30 days, stored hashed in `refresh_tokens`)
- [ ] `POST /api/v1/auth/refresh` — rotates the refresh token, returns new access token
- [ ] `POST /api/v1/auth/logout` — revokes the refresh token
- [ ] `GET /api/v1/auth/me` — current user + their clinic memberships (a user can belong to more than one clinic; the frontend picks/remembers an active clinic)
- [ ] Google OAuth (per `mvp.md` §6.1 "optional") — stub the endpoint shape now (`POST /api/v1/auth/google`), implement fully only if a pilot clinic asks for it before Phase 19; do not block this phase on it
- [ ] Password hashing: argon2 or bcrypt via `passlib`
- [ ] `app/core/security.py` — JWT encode/decode helpers, `get_current_user` FastAPI dependency, `require_clinic_role(*roles)` dependency factory that resolves the active clinic from a header/path param and checks the caller's `clinic_memberships` row — **this dependency is what every future endpoint uses for RBAC, never a manual `if` check duplicated per route**

### 5. Frontend (`apps/web`)

- [ ] `src/features/auth/` — login page, register page, RHF+Zod forms
- [ ] `src/lib/auth.ts` — token storage (httpOnly cookie preferred over localStorage; if localStorage is used for the access token during early dev, document the tradeoff and revisit before Phase 19's production readiness sign-off), auto-refresh on 401
- [ ] Route guard — unauthenticated users redirected to `/login`; a signed-in user with zero clinic memberships redirected into the onboarding wizard (Phase 3) instead of a dead dashboard
- [ ] `packages/api-client` regenerated against the real `auth` OpenAPI paths once they exist (first real use of the Orval pipeline)

## Data model

New tables: `clinics`, `users`, `clinic_memberships`, `refresh_tokens`, `activity_log`. See `docs/architecture/data-model.md` for the full-project entity map this phase seeds.

## API endpoints

| Method | Path                    | Auth          | Notes                                    |
| ------ | ----------------------- | ------------- | ---------------------------------------- |
| GET    | `/api/v1/health`        | none          | liveness check                           |
| POST   | `/api/v1/auth/register` | none          | creates user + clinic + owner membership |
| POST   | `/api/v1/auth/login`    | none          |                                          |
| POST   | `/api/v1/auth/refresh`  | refresh token | rotates token                            |
| POST   | `/api/v1/auth/logout`   | access token  | revokes refresh token                    |
| GET    | `/api/v1/auth/me`       | access token  |                                          |

## Edge cases & safety

- Refresh token reuse after rotation (stolen/replayed token) must revoke the whole token family, not just fail silently — log to `activity_log` with actor_type `system`.
- Registering with an email that already exists must not leak whether the email exists (generic error) — standard account-enumeration hygiene.
- A `clinic_memberships` row with `is_active = false` (e.g. removed staff) must fail auth checks even if the JWT is still technically valid and unexpired — always re-check membership state per request, never trust only the JWT claims.
- CORS: `apps/web` origin only, credentials allowed if using httpOnly cookies.
- Never trust a client-supplied `clinic_id` anywhere, including in this phase's own endpoints that don't obviously need it yet — establish the pattern now.

## Testing

- pytest: register → login → refresh → logout happy path; expired/invalid token rejection; inactive membership rejection; refresh-token-reuse detection
- Vitest: login form validation, auth redirect logic
- `pnpm run ci:quality` green

## Docs to update in this phase

- `docs/architecture/monorepo-structure.md` — confirm actual paths match what was planned, correct any drift
- `docs/architecture/data-model.md` — mark `clinics`/`users`/`clinic_memberships`/`refresh_tokens`/`activity_log` as shipped
- `docs/architecture/api-conventions.md` — first real example of the request/response/error shape
- `docs/guides/routes/README.md` — create the directory + index (empty template ready for Phase 3's first real page guide)
- `CLAUDE.md` — flip any "not scaffolded yet" language once true; confirm command list matches reality
- Root `README.md` — update "Status" line once scaffolding lands

## Exit criteria

- [ ] `pnpm install && pnpm run dev:docker && pnpm run dev` boots web + api + worker with no manual steps beyond `.env` setup
- [ ] A new user can register, land in an empty-state dashboard shell (or onboarding redirect), log out, log back in
- [ ] `alembic upgrade head` runs clean against a fresh Docker Postgres
- [ ] RBAC dependency (`require_clinic_role`) exists and is unit-tested even though no protected resource-specific endpoint uses it yet beyond auth
- [ ] CI pipeline green on a trivial PR
- [ ] `activity_log` table exists (empty is fine — first write lands in Phase 3)
