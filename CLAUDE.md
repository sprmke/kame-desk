# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository. Cursor and OpenCode read it too (see `.cursor/rules/README.md` / `.opencode/README.md`) — treat it as the single always-loaded agent context for this repo.

## What this is

**DoctorDesk (kame-desk)** — a clinic management platform for independent doctors and small clinics. Core loop: front desk books an appointment, patient arrives, doctor writes a SOAP note and issues prescriptions, billing records payment, reminders/recalls keep patients coming back. Layered on top: an **AI Clinic Assistant** — a chat panel that can execute real dashboard actions (book, reschedule, draft a SOAP note, check a balance, generate a certificate) instead of the user clicking through screens, with a tiered risk model and full audit trail.

Full product scope: **`docs/mvp.md`** (authoritative PRD — read before any module work). Stack: **`docs/tech-stack.md`** (authoritative — read before any infra/tooling decision). Build plan: **`docs/phases/README.md`** (read before starting any phase).

Stack: **pnpm + Turborepo monorepo**. Frontend `apps/web` (React 19 + TanStack Start + Vite + TypeScript). Backend `apps/api` (FastAPI/Python, always-on, owns **all** business logic — visits, scheduling rules, SOAP writes, AI, WebSockets, background jobs). Postgres via Neon + pgvector, SQLAlchemy 2 (async) + Alembic migrations — no ORM-free raw SQL, no Prisma/Drizzle. Redis + ARQ for background jobs. Cloudflare R2 for files. No Supabase, no tRPC, no Next.js — see `docs/tech-stack.md` § Explicitly out of scope.

**This repo does not inherit kame-homes' backend** (that's Deno/Supabase). It **does** reuse kame-homes' hardened _patterns_: tiered-risk AI tool-calling, draft-then-confirm AI writes, append-only audit log, RBAC re-checked server-side per request, doc-sync discipline, and the Cursor/Claude/OpenCode AI-tooling setup itself (this file, `.cursor/`, `.claude/`, `.opencode/`, skills, hooks) — adapted to this stack.

## AI session hygiene

See **`.cursor/rules/ai-usage.mdc`** (always-on in Cursor; follow here too):

- **One task ≈ one session** — `/clear` when switching goals; avoid multi-day threads.
- **No subagent swarms by default** — Explore/Plan/debugger/security-auditor only when asked or clearly necessary.
- Prefer `/effort medium` for routine chores; reserve high effort + thinking for hard architecture/AI-safety judgment calls.
- Heavy rules (`appointment-workflow.mdc`, `ai-assistant-safety.mdc`, `fastapi-conventions.mdc`, `tanstack-start-conventions.mdc`, `anti-slop-design.mdc`) are **glob-scoped, not always-on** — read them when the task touches those surfaces.

## Commands

Scaffolding for these lands in **Phase 1** (`docs/phases/phase-01-monorepo-scaffold.md`); the commands below are the target shape once that phase ships — check `package.json` for what currently exists.

```bash
pnpm install
pnpm run setup:ai-tooling        # once after clone
pnpm run dev:docker              # Postgres+pgvector, Redis, MinIO (R2 stand-in), Mailhog
pnpm run dev                     # web + api + worker together (./dev.sh)
pnpm run dev:web                 # apps/web only (Vite dev server)
pnpm run dev:api                 # apps/api only (uvicorn --reload)
pnpm run dev:worker               # ARQ worker only (transcription, embeddings, recurring expand)

pnpm run lint / lint:fix / type-check / build / test
pnpm run format / format:check   # Prettier (TS) + ruff format (Python)
pnpm run check:filenames         # naming conventions
pnpm run check:design-slop       # anti-slop ratchet (mechanical)
pnpm run capture:design-screenshots  # 375/820/1440 × light/dark (needs local app)
pnpm run ci:quality              # everything CI runs — run before every PR

pnpm run db:migrate               # apps/api: alembic upgrade head (local Postgres only)
pnpm run db:migrate:new           # apps/api: alembic revision --autogenerate — review before committing
pnpm run db:seed                  # local dev seed data (never real patient data)
pnpm run db:reset:local           # drop + recreate local DB + migrate + seed

pnpm run deploy:api:dev / deploy:web:dev     # dev environment — safe, no unlock needed
pnpm run deploy:api:prod / deploy:web:prod   # PRODUCTION — deskwave unlock required for agents
pnpm run migrate:prod                        # remote Alembic upgrade against prod Neon — deskwave required
pnpm run backup:db:dev / :prod               # pre-deploy backups (also automatic before deploy)
pnpm run rollback:db:dev / :prod             # restore most recent backup (prod: deskwave required)
pnpm run env:status                          # which DATABASE_URL / environment is active
```

CI (`.github/workflows/ci.yml`, added in Phase 1): type-check, lint, `check:filenames`, build, backend tests (pytest), frontend tests (Vitest) — Playwright E2E runs on a separate, slower job once E2E specs exist (Phase 3+).

### Local dev gotchas (fill in as they're discovered)

- **API `dev` / `worker` must use `uv run`.** macOS has `python3` and `uv`, not a `python` or `uvicorn` on PATH. `pnpm run migrate` already used `uv run`; `dev` and `worker` now do too. If those scripts are ever changed back to bare `uvicorn` / `python`, `pnpm run dev` will fail with `command not found`.
- **`apps/api` has no `node_modules`.** That pnpm warning is expected: the API is a Python package; `uv sync` owns its env.
- **Local dev URLs.** Web **http://localhost:3100** · API **http://localhost:8100** (fixed ports to avoid clashes with other projects on 3000/8000). `strictPort` is on; if 3100 is taken, stop the other process.

## Architecture

```
apps/web (Cloudflare Pages)          apps/api (Hetzner VPS, always-on)
React + TanStack Start + Vite   →    uvicorn → FastAPI (REST /api/v1 + WebSockets + SSE)
TanStack Query · RHF + Zod           arq worker (transcription, embeddings, recurring expand)
WebSocket client                     Redis (same host)
                                            │
                          ┌─────────────────┼─────────────────┐
                          ▼                 ▼                 ▼
                    Neon Postgres    Cloudflare R2      LLM APIs
                    + pgvector       (files / audio)    (OpenAI / Gemini)
```

Full diagram + invariants: `docs/tech-stack.md` § Architecture. Directory-level layout: `docs/architecture/monorepo-structure.md`.

| Path                              | Role                                                                             |
| --------------------------------- | -------------------------------------------------------------------------------- |
| `apps/web/src/routes/`            | TanStack Router file-based routes (thin — compose features)                      |
| `apps/web/src/features/{module}/` | Feature folders: `components/`, `hooks/`, `lib/`, `pages/`                       |
| `apps/api/app/routers/`           | FastAPI routers — one per resource, mounted under `/api/v1`                      |
| `apps/api/app/services/`          | Business logic — the only place that writes DB state                             |
| `apps/api/app/models/`            | SQLAlchemy 2 ORM models                                                          |
| `apps/api/app/schemas/`           | Pydantic v2 request/response schemas (source of the OpenAPI spec)                |
| `apps/api/app/workers/`           | ARQ job definitions (transcription, embeddings, reminders, recurring expand)     |
| `apps/api/migrations/`            | Alembic migrations — plain SQL-generated, never edit a shipped one               |
| `packages/api-client/`            | Orval-generated TypeScript client + TanStack Query hooks from the OpenAPI schema |
| `docs/`                           | Doc index at `docs/README.md`                                                    |
| `docs/phases/`                    | The build plan — read the current phase file before starting work                |

### Multi-doctor / clinic scoping

Every table that isn't global (`clinics`, platform-level lookups) carries a `clinic_id` and every query is scoped through the authenticated user's clinic membership — never trust a client-supplied `clinic_id`. Roles are clinic-scoped: `owner`, `admin`, `doctor`, `reception` (see `docs/mvp.md` §6.11 for the full permission matrix). A clinic can have 2+ doctors sharing one front desk and one patient registry (`docs/mvp.md` §7.1) — do not assume single-doctor when building scheduling or patient search.

### Appointment / visit status workflow

Two separate lifecycles, not one flat list:

- **Appointment status** (pre-visit): `Scheduled → Confirmed → Cancelled / No Show / Rescheduled`
- **Visit status** (day-of): `Arrived → In Consultation → Completed`

Double-booking prevention is a **Postgres exclusion constraint** (`btree_gist`, per doctor/room), not just UI validation. Canonical spec: `docs/mvp.md` §6.4 and (once written) `.cursor/rules/appointment-workflow.mdc`. All transitions go through a single service function — never duplicate side-effect logic (reminders, calendar sync, audit log) in a route handler.

### AI Clinic Assistant — safety model (read before touching any AI tool)

Three-tier risk model, **server-computed, never model-decided**: Tier 0 read-only (always allowed if RBAC passes), Tier 1 auto-executed (idempotent, low blast radius), Tier 2 confirm-required (the tool returns a proposal; nothing writes until the user taps Confirm). Clinical writes (SOAP, prescriptions, diagnoses) and any real message sent to a patient are **always** Tier 2, no exceptions. Full spec: `docs/mvp.md` §9 and `docs/architecture/ai-clinic-assistant.md` — **read both before adding or changing an assistant tool.** This mirrors kame-homes' AI Dashboard Assistant pattern, hardened across a comparable production surface.

### Auth — don't conflate these tiers

| Tier                   | Gate                                               | Notes                                                                                        |
| ---------------------- | -------------------------------------------------- | -------------------------------------------------------------------------------------------- |
| Clinic user            | JWT access + refresh (FastAPI-issued)              | `owner` / `admin` / `doctor` / `reception`, clinic-scoped                                    |
| Public/guest           | none, or a booking-link token                      | Public self-service booking page (`docs/mvp.md` §7.3) — never exposes another patient's data |
| AI assistant tool call | Same JWT as the calling user, re-verified per tool | Never trust model-asserted identity or IDs — re-check against the real token every call      |

RBAC is enforced **server-side in FastAPI**, never only in the UI and never assumed from a DB constraint alone.

## Conventions

- **Dates/times:** all patient-facing times in **Asia/Manila**. API dates `YYYY-MM-DD` (ISO 8601), timestamps UTC in the DB, converted at the edge.
- **Naming:** Python `snake_case.py` modules, `PascalCase` SQLAlchemy models, `PascalCase` Pydantic schemas suffixed by intent (`PatientCreate`, `PatientRead`, `PatientUpdate`). TS/React: `PascalCase.tsx` components, `useX.ts` hooks, `camelCase.ts` lib files, TanStack Router file routes per its own convention. Full rules: `.cursor/rules/naming-conventions.mdc`.
- **Secrets:** `apps/api/.env` (gitignored) locally; VPS env / secrets manager in production. Never commit or log credentials, tokens, or PHI (patient data).
- **PHI/PII:** never log patient content in plaintext, never send it to error tracking (Sentry) payloads, never paste it into chat/AI tool context beyond what a tool call strictly needs. See `.cursor/rules/phi-data-safety.mdc`.
- **Migrations:** Alembic only. Never edit a shipped migration under `apps/api/migrations/versions/` — add a new one. See `.cursor/rules/migrations.mdc`.
- **Testing:** pytest + httpx + pytest-asyncio (API), Vitest + Testing Library (web), Playwright (E2E — calendar/status flows). Write tests alongside the phase that introduces the surface, not as a separate backlog item.
- **Mobile:** every screen usable at 375–1024px+, 44×44px touch targets. Below `lg`: `BottomTabBar` (Calendar / Waiting / Patients / More) + `ResponsiveModal` sheets. Tokens: `apps/web/src/lib/motion.ts`. Cursor: `mobile-responsive.mdc` / `components.mdc` / `motion.mdc`; Claude: invoke the matching skills.
- **Copy:** prefer no extra UI prose (`ui-minimal-copy.mdc`). When text is required, keep it short, plain, production-grade, no AI tells, no em dashes (`human-copy.mdc`).

## Plan mode

When planning without implementing (Cursor Plan mode, or the user asks for a plan only): do not write code, save the finished plan to `docs/workflow/planned/<slug>.md` (no date prefix), add a row to `docs/workflow/planned/README.md`. See `.cursor/rules/plan-mode.mdc`.

## Docs are the source of truth

Whenever you implement or materially change behavior (features, routes, validation, API endpoints, DB schema/migrations, env vars, integrations, AI tools, or user-visible flows), **update documentation in the same change** — not as a follow-up the user must request.

**Before claiming any material task done:**

1. Invoke/follow **`documentation-maintenance`** (skill or rule).
2. If a page/section/route changed → also update the matching **`docs/guides/routes/*.md`** guide (`route-guides`).
3. If the change mutates clinic/patient/appointment state (API write, workflow transition, cron, webhook, AI-assistant write) → emit an `activity_log` event or write `activity-log: N/A — <why>` (`audit-logging`).
4. If you added or changed an AI assistant tool → update `docs/architecture/ai-clinic-assistant.md`'s tool catalog table and confirm the tier classification (`ai-clinic-assistant` skill / `ai-assistant-safety.mdc`).
5. If you completed a phase's tasks → check its exit criteria in `docs/phases/<phase-file>.md` and update `docs/phases/README.md`'s status table.

| Change                                                      | Update                                                                     |
| ----------------------------------------------------------- | -------------------------------------------------------------------------- |
| Architecture, routes, env vars, API surface, data model     | `docs/architecture/*.md` (pick the matching file)                          |
| Page/section behavior, save flows, validation, per-route UX | `docs/guides/routes/*.md`                                                  |
| Appointment/visit status, orchestrator, side-effects        | `.cursor/rules/appointment-workflow.mdc` (canonical once written)          |
| AI Clinic Assistant tools, tiers, safety checks             | `docs/architecture/ai-clinic-assistant.md` + `docs/mvp.md` §9              |
| Database migration or one-shot backfill instructions        | `docs/architecture/deployment.md` § migrations                             |
| Product scope change                                        | `docs/mvp.md` (this is the PRD — keep it in sync with what actually ships) |
| Phase progress                                              | `docs/phases/README.md` status table + the phase file's checklist          |

Trivial fixes (typos, internal renames with no behavior/API/UX impact) don't need doc updates. Full skills/rules index: `.cursor/rules/README.md` (Cursor) · `.claude/README.md` (Claude Code) · `.opencode/README.md` (OpenCode).

## Agent tooling

Index: `.claude/README.md` (Claude Code) · `.cursor/rules/README.md` (Cursor) · `.opencode/README.md` (OpenCode) + root `opencode.json`. Skills live in `.agent/skills/` (canonical, symlinked into `.cursor/skills/` + `.claude/skills/`). Subagents: `debugger`, `security-auditor`, `test-runner`, `verifier`, `design-reviewer`. Commands: `/dd-*` (start with `/dd-help`). Design review: `/dd-design-review`. MCP servers: `context7`, `markitdown`, `playwright`, `postgres` (local dev DB only — see `.mcp.json`).

## Don'ts

- Next.js, App Router, tRPC, Drizzle, GraphQL, gRPC, Supabase-as-BaaS, MongoDB, Clerk/Auth0, bun (package manager) — see `docs/tech-stack.md` § Explicitly out of scope.
- Business logic in `apps/web` server functions/loaders — FastAPI owns all business logic; TanStack Start owns UI only.
- Side effects (reminders, calendar, audit log) inline in a route handler — go through the relevant service function.
- Editing a shipped Alembic migration under `apps/api/migrations/versions/` — add a new one.
- The AI assistant writing anything without a human confirm for Tier 2 actions (clinical writes, patient messages, billing) — no exceptions, no "trusted user" bypass.
- Logging or emailing raw patient data (PHI) in error tracking, AI prompts beyond what's needed, or debug output.
- **Production deploys or migrations without unlock** — `.cursor/rules/no-prod-deploy.mdc`. Never run or recommend `deploy:api:prod`, `deploy:web:prod`, `migrate:prod`, or any write against the prod Neon `DATABASE_URL` unless the user said **`deskwave`** in the same message. Shell hooks enforce this.
- Attributing commits to Cursor/Claude/AI tooling — `.cursor/rules/git-commits.mdc`.
