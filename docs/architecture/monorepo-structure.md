# Monorepo structure

Standing reference for directory layout and where new code belongs. See `docs/tech-stack.md` for the technology choices this structure implements, and `docs/phases/README.md` for when each part gets built.

## Top level

```
kame-desk/
├── apps/
│   ├── web/                 # React 19 + TanStack Start + Vite + TypeScript
│   └── api/                 # FastAPI (Python) — owns all business logic
├── packages/
│   └── api-client/          # Orval-generated TS client + TanStack Query hooks from apps/api's OpenAPI schema
├── docs/                    # This documentation tree — see docs/README.md
├── scripts/
│   ├── dev/                 # Local dev + quality-gate scripts (setup-ai-tooling, ci-quality-gate, db-reset-local, env-status, check-filenames)
│   └── deploy/               # Deploy/backup/rollback/migrate-remote scripts (dev + prod targets)
├── .cursor/, .claude/, .opencode/, .agent/   # AI agent tooling — see docs/phases/phase-00-ai-tooling-and-agent-setup.md
├── .github/workflows/       # CI
├── .vscode/tasks.json       # Run tasks (Cmd/Ctrl+Shift+P → "Tasks: Run Task")
├── docker-compose.yml       # Local dev infra: Postgres+pgvector, Redis, MinIO (R2 stand-in), Mailhog
├── turbo.json, pnpm-workspace.yaml, package.json
├── dev.sh                   # Orchestrates full local stack
└── CLAUDE.md                # Always-loaded agent context
```

## `apps/web` (frontend)

```
apps/web/
├── src/
│   ├── routes/                    # TanStack Router file-based routes — thin, compose features only
│   │   ├── __root.tsx
│   │   ├── login.tsx, register.tsx
│   │   ├── book.$clinicSlug.tsx   # Public self-service booking (Phase 4)
│   │   └── dashboard/             # Authenticated shell + nested routes per module
│   ├── features/
│   │   └── {module}/
│   │       ├── components/        # Feature-scoped React components
│   │       ├── hooks/             # useX.ts — TanStack Query hooks, local feature hooks
│   │       ├── lib/                # camelCase.ts — schemas (Zod), pure helpers
│   │       └── pages/              # Page-level components composed by a route
   │   ├── components/ui/             # shadcn/ui primitives (not feature-specific)
   │   ├── components/list/           # Shared list chrome: ManagedList, search, sort, views, pagination
   │   ├── components/theme/          # ThemeProvider + ThemeToggle (light/dark/system)
   │   ├── hooks/                     # Cross-feature hooks (useListSearch URL state)
   │   ├── lib/                       # Cross-feature: apiClient.ts, queryClient.ts, auth.ts, websocket.ts, theme/, list/
│   └── main.tsx
├── public/
├── vite.config.ts, tsconfig.json (path alias `@/` → `apps/web/src/`)
```

**Modules under `src/features/`** (populated phase by phase — see `docs/phases/README.md`): `auth`, `onboarding`, `settings` (team, notifications, document-templates), `patients`, `appointments` (+ `calendar/`, `waiting-room`), `soap`, `prescriptions`, `billing`, `documents`, `recalls`, `reports`, `audit-log`, `chart-search`, `assistant`.

Rules: no barrel `index.ts` re-exports across features; `appointments` is not a junk drawer, related-but-distinct UI (waiting room, calendar) gets its own subfolder or its own feature; no business logic in a TanStack Start server function or loader — it calls `apps/api`, it does not reimplement scheduling/SOAP/billing rules itself.

## `apps/api` (backend)

```
apps/api/
├── app/
│   ├── main.py              # App factory, CORS, router mounting, exception handlers
│   ├── core/
│   │   ├── config.py        # Pydantic Settings from env
│   │   ├── db.py             # Async SQLAlchemy engine/session factory
│   │   ├── pagination.py    # page/page_size clamp, sort parse, paginate()
│   │   └── security.py      # JWT encode/decode, password hashing, RBAC dependencies
│   ├── routers/              # One per resource, mounted under /api/v1 — thin: parse request, call a service, return a schema
│   ├── services/              # ALL business logic and DB writes live here — the only place that writes DB state
│   ├── models/                # SQLAlchemy 2 ORM models (PascalCase classes, snake_case.py files)
│   ├── schemas/                # Pydantic v2 request/response schemas (XCreate/XRead/XUpdate naming)
│   ├── workers/                # ARQ job definitions (transcription, embeddings, reminders, recurring expand)
│   └── ai/
│       ├── assistant/          # Staff-facing AI Clinic Assistant (Phase 16) — context, tiers, safety, tools
│       ├── patient_assistant/  # Patient-facing booking/FAQ assistant (Phase 18) — separate, more restricted
│       └── prompts/, schemas.py
├── migrations/                 # Alembic — plain SQL-generated, never edit a shipped one
├── tests/                       # pytest + httpx + pytest-asyncio, mirrors app/ structure
├── pyproject.toml               # uv-managed; ruff (lint+format), pytest config
└── .env.example
```

**Layering rule (non-negotiable):** `routers/` → `services/` → `models/`. A router never talks to the DB directly; a service function is the single place a given piece of business logic exists, called by routers, ARQ workers, and AI tools alike — this is what makes Phase 16's AI tools thin wrappers instead of parallel reimplementations.

## `packages/api-client`

Generated, not hand-written. Regenerated via `pnpm run db:generate-client` (exports `apps/api`'s OpenAPI schema, runs Orval). Never hand-edit generated files; if a generated shape is wrong, fix the FastAPI schema and regenerate.

## Naming conventions (full rules: `.cursor/rules/naming-conventions.mdc`, created in Phase 0)

| Context               | Convention                            | Example                                         |
| --------------------- | ------------------------------------- | ----------------------------------------------- |
| Python modules        | `snake_case.py`                       | `appointment_service.py`                        |
| SQLAlchemy models     | `PascalCase` class in `snake_case.py` | `class Appointment` in `appointment.py`         |
| Pydantic schemas      | `PascalCase` suffixed by intent       | `PatientCreate`, `PatientRead`, `PatientUpdate` |
| React components      | `PascalCase.tsx`                      | `AppointmentCard.tsx`                           |
| React hooks           | `useX.ts`                             | `useAppointments.ts`                            |
| TS lib/schema files   | `camelCase.ts`                        | `appointmentSchema.ts`                          |
| TanStack Router files | Router's own file-route convention    | `dashboard.patients.$patientId.tsx`             |

## Where to edit (quick pointer table — full version in `CLAUDE.md`)

| Concern                       | Path                                                                              |
| ----------------------------- | --------------------------------------------------------------------------------- |
| Patient/appointment/visit API | `apps/api/app/routers/`, `apps/api/app/services/`                                 |
| SOAP / clinical records       | `apps/api/app/services/soap_service.py` (versioned writes, never in-place update) |
| AI Clinic Assistant           | `apps/api/app/ai/assistant/` + `apps/web/src/features/assistant/`                 |
| Patient-facing assistant      | `apps/api/app/ai/patient_assistant/`                                              |
| DB schema                     | `apps/api/app/models/` + `apps/api/migrations/versions/`                          |
| Web feature UI                | `apps/web/src/features/{module}/`                                                 |
| Web routes                    | `apps/web/src/routes/` (thin — compose features)                                  |
