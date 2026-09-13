# Tech stack

Authoritative technology choices for **DoctorDesk** (kame-desk). Update this file when the stack changes.

For **what to build** (modules, MVP scope, AI Clinic Assistant spec, production readiness checklist), see [`mvp.md`](./mvp.md) — that doc is the authoritative PRD; this doc stays scoped to _how_.

**Last updated:** 2026-09-11

## Summary

| Layer        | Choice                                     |
| ------------ | ------------------------------------------ |
| Monorepo     | pnpm workspaces + Turborepo                |
| Frontend     | React + TanStack Start + Vite + TypeScript |
| Backend      | FastAPI (Python), always-on server         |
| API contract | REST `/api/v1` + OpenAPI                   |
| Database     | PostgreSQL (Neon) + pgvector               |
| Jobs / cache | Redis + ARQ on the API host                |
| Realtime     | FastAPI WebSockets                         |
| Files        | Cloudflare R2                              |
| Web host     | Cloudflare Pages                           |
| API host     | Hetzner VPS                                |

## Architecture

TanStack Start owns **UI only**. FastAPI owns **all business logic**: visits, scheduling rules, SOAP writes, AI, WebSockets, and background jobs.

```
┌─────────────────────────────────────────────────────────────┐
│  Cloudflare Pages                                           │
│  React + TanStack Start + Vite                              │
│  TanStack Query · WebSocket client · RHF + Zod              │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTPS  REST /api/v1
                           │ WSS    /ws/clinic/{id}
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  Hetzner VPS (always-on)                                    │
│  ├─ uvicorn → FastAPI (API + WebSockets + SSE for AI)       │
│  ├─ arq worker (transcribe, embeddings, recurring expand)   │
│  └─ Redis (on same host)                                    │
└──────────────────────────┬──────────────────────────────────┘
                           │
         ┌─────────────────┼─────────────────┐
         ▼                 ▼                 ▼
    Neon Postgres    Cloudflare R2      LLM APIs
    + pgvector       (files / audio)    (OpenAI / Gemini)
```

### Invariants

- Do not duplicate visit transitions or SOAP saves in TanStack Start server functions.
- AI output is a **draft**; a doctor **confirms** before a versioned chart save.
- Store blobs (PDF, audio, images) in R2, not in Postgres bytea columns.
- Log mutations to an append-only activity log. Never log PHI.

## Monorepo

| Piece            | Technology                                             |
| ---------------- | ------------------------------------------------------ |
| Layout           | `apps/web`, `apps/api`, `packages/api-client`          |
| Package manager  | **pnpm**                                               |
| Task runner      | **Turborepo**                                          |
| Python tooling   | **uv** (or `venv` + `pip`) in `apps/api`               |
| Shared API types | **Orval** (OpenAPI → TS client + TanStack Query hooks) |

Do not mix pnpm and bun in this repo.

## Frontend (`apps/web`)

| Concern           | Technology                                                                                                                       |
| ----------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| Framework         | React 19 + TanStack Start + Vite + TypeScript                                                                                    |
| Routing           | TanStack Router (via Start)                                                                                                      |
| Server state      | TanStack Query v5                                                                                                                |
| Tables            | TanStack Table                                                                                                                   |
| Forms             | React Hook Form + Zod                                                                                                            |
| Styling           | Tailwind CSS + shadcn/ui                                                                                                         |
| Calendar          | Schedule-X (MIT) or FullCalendar resource view                                                                                   |
| Drag-and-drop     | dnd-kit                                                                                                                          |
| Dates / recurring | date-fns + rrule                                                                                                                 |
| Realtime          | WebSocket client → TanStack Query invalidation                                                                                   |
| AI streaming      | EventSource (SSE) into SOAP fields                                                                                               |
| Icons             | Lucide                                                                                                                           |
| Toasts            | Sonner                                                                                                                           |
| Motion            | CSS (`tw-animate-css` + theme keyframes) + **framer-motion** for sliding pills, list stagger, and dashboard page transition only |

**Explicitly chosen:** `framer-motion` (~scoped to `SlidingActivePill`, `PageTransition`, command-palette stagger). Not used for hover micro-interactions. `vite-plugin-pwa`/workbox stay deferred — Phase 36's read-only offline cache is a hand-rolled ~40-line `apps/web/public/sw.js` (network-first with cache fallback for the appointments/patients list endpoints only), not a full PWA toolchain. See `docs/architecture/offline-resilience.md`.

**Deploy:** Cloudflare Pages (static SPA or light SSR shell).

## Backend (`apps/api`)

| Concern           | Technology                                              |
| ----------------- | ------------------------------------------------------- |
| Framework         | FastAPI                                                 |
| Validation        | Pydantic v2                                             |
| ORM               | SQLAlchemy 2 (async)                                    |
| Migrations        | Alembic                                                 |
| Server            | uvicorn (gunicorn + workers in prod if needed)          |
| API style         | REST `/api/v1`, auto OpenAPI schema                     |
| Auth              | JWT access + refresh tokens                             |
| Roles             | `reception`, `doctor`, `owner`, `admin` (clinic-scoped) |
| Realtime          | FastAPI WebSockets (`appointment.*` events)             |
| AI orchestration  | PydanticAI (structured SOAP output)                     |
| Speech            | faster-whisper on ARQ worker (Deepgram later if needed) |
| Task queue        | ARQ                                                     |
| HTTP client (LLM) | httpx                                                   |

**Deploy:** Hetzner VPS (CX22 to start). Same machine runs API, ARQ worker, and Redis.

### Why always-on

The live waiting room uses WebSockets. Background jobs (transcription, embedding, large recurring expansion) use an ARQ worker. A small fixed VPS is cheaper and simpler than polling or splitting workers across serverless for steady clinic-hours traffic.

## Database

| Piece          | Technology                                          |
| -------------- | --------------------------------------------------- |
| Engine         | PostgreSQL 16                                       |
| Host           | Neon (free tier, then scale plan)                   |
| Vector search  | pgvector                                            |
| Double-booking | `btree_gist` exclusion constraint per doctor / room |
| Migrations     | Alembic only; never edit shipped migrations         |

### Core tables (v1)

- `clinics`, `users`, `patients`
- `appointments`, `appointment_series`
- `visit_status_events`
- `soap_notes` (versioned rows)
- `vitals`
- `activity_log` (append-only audit)

## Files, email, SMS, WhatsApp

| Concern        | Technology                                                           |
| -------------- | -------------------------------------------------------------------- |
| Object storage | Cloudflare R2                                                        |
| File access    | Presigned URLs issued by FastAPI                                     |
| Email          | Resend                                                               |
| SMS            | Twilio (optional, clinic opt-in)                                     |
| WhatsApp       | Meta WhatsApp Business Cloud API (Phase 35, optional, clinic opt-in) |

Messaging channels (email/SMS/WhatsApp) sit behind a shared adapter interface (`app/services/messaging/`) so a future channel (Messenger, Viber) can be added without touching the reminder-scheduling logic — see `docs/architecture/messaging-channels.md`.

## AI (cost-aware defaults)

| Use              | Approach                                      |
| ---------------- | --------------------------------------------- |
| SOAP draft       | PydanticAI + GPT-4o-mini or Gemini Flash      |
| Complex finalize | Stronger model only on explicit user action   |
| Streaming        | SSE from FastAPI                              |
| Transcription    | ARQ + faster-whisper on VPS                   |
| Chart search     | pgvector embeddings after SOAP save (ARQ job) |
| Safety           | Draft → doctor confirm → versioned save       |
| Cost control     | Per-clinic daily AI cap in app settings       |

LLM and transcription usage usually cost more than hosting. Cap and meter AI per clinic.

## Security and audit

| Concern       | Approach                                                             |
| ------------- | -------------------------------------------------------------------- |
| Transport     | HTTPS everywhere                                                     |
| Secrets       | `.env` locally; Doppler or VPS env in production                     |
| SOAP access   | Doctor (and owner) write; reception read policy per product decision |
| Audit         | `activity_log` on every mutation                                     |
| SOAP history  | Version rows; no in-place overwrite                                  |
| Observability | Sentry (web + API); structured JSON logs without PHI                 |

## Testing and CI

| Layer | Tool                                |
| ----- | ----------------------------------- |
| API   | pytest + httpx + pytest-asyncio     |
| Web   | Vitest + Testing Library            |
| E2E   | Playwright (calendar + status flow) |
| CI    | GitHub Actions                      |

## Local development

| Piece        | Technology                                                        |
| ------------ | ----------------------------------------------------------------- |
| Containers   | Docker Compose: Postgres, Redis, MinIO (R2 stand-in)              |
| API          | `uv run uvicorn --reload` (never bare `uvicorn`/`python` on PATH) |
| Web          | TanStack Start dev server                                         |
| Entry script | `./dev.sh` (planned)                                              |

## Hosting and estimated infra cost

| Service          | Role                | Est. cost (early) |
| ---------------- | ------------------- | ----------------- |
| Hetzner CX22     | API + ARQ + Redis   | €4–6 / mo         |
| Neon             | Postgres + pgvector | $0 free tier      |
| Cloudflare Pages | Web app             | $0                |
| Cloudflare R2    | Files               | $0 free tier      |
| Resend           | Email               | $0 free tier      |
| Sentry           | Errors              | $0 free tier      |

**MVP infra:** about $5–15 / month before LLM and SMS usage.

## Explicitly out of scope (v1)

| Skip                  | Reason                                |
| --------------------- | ------------------------------------- |
| tRPC                  | Python backend; use OpenAPI instead   |
| GraphQL / gRPC        | REST is enough for one clinic SPA     |
| Clerk / Auth0         | JWT in FastAPI; free at scale         |
| Supabase as full BaaS | FastAPI is the backend                |
| Django / NestJS       | FastAPI is locked                     |
| Serverless API        | Always-on VPS chosen for WS + workers |
| MongoDB               | Postgres + constraints + pgvector     |
| bun (package manager) | pnpm chosen for this monorepo         |

## Build order

1. Monorepo scaffold + Docker Compose + auth
2. Patients + appointments + exclusion constraint
3. Day calendar + drag reschedule
4. Status board + WebSockets
5. Walk-in, reschedule, no-show
6. Recurring series (rrule + ARQ expand)
7. SOAP versions + vitals + follow-up
8. PydanticAI draft + SSE
9. Transcription + pgvector search

## Related repos

- **kame-homes:** separate product (React + Vite + Supabase). Different stack on purpose.
- This workspace may include kame-homes for reference; DoctorDesk does not inherit its backend.

## Decision log

| Date       | Decision                                                                         |
| ---------- | -------------------------------------------------------------------------------- |
| 2026-09-08 | React + TanStack Start + Vite frontend                                           |
| 2026-09-08 | FastAPI backend (Python for AI)                                                  |
| 2026-09-08 | Always-on Hetzner VPS (API + ARQ + Redis)                                        |
| 2026-09-08 | pnpm monorepo (not bun)                                                          |
| 2026-09-08 | Cost-conscious managed services: Neon, Cloudflare Pages/R2, self-hosted JWT auth |
