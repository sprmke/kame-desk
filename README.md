# DoctorDesk

**A clinic management platform for independent doctors and small clinics: scheduling, live visit status, SOAP records, prescriptions, billing, and an AI assistant that can execute real dashboard actions by chat.**

Built as a **pnpm + Turborepo** monorepo: **React 19** and **TanStack Start** on the front end, **FastAPI** on the back end (all business logic server-side), **PostgreSQL** with **pgvector**, **Redis + ARQ** for background jobs, and **WebSockets** for the live waiting room. Designed for Philippine private clinics: Asia/Manila times, payer workflows, and operational density over marketing chrome.

<p align="center">
  <a href="#features">Features</a> ·
  <a href="#screenshots">Screenshots</a> ·
  <a href="#tech-stack">Tech Stack</a> ·
  <a href="#getting-started">Getting Started</a> ·
  <a href="#documentation">Documentation</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/React-19-61dafb?style=flat-square&logo=react" alt="React" />
  <img src="https://img.shields.io/badge/TanStack_Start-000?style=flat-square" alt="TanStack Start" />
  <img src="https://img.shields.io/badge/TypeScript-5-3178c6?style=flat-square&logo=typescript" alt="TypeScript" />
  <img src="https://img.shields.io/badge/Tailwind-4-38bdf8?style=flat-square&logo=tailwindcss" alt="Tailwind" />
  <img src="https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi" alt="FastAPI" />
  <img src="https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python" alt="Python" />
  <img src="https://img.shields.io/badge/PostgreSQL-4169E1?style=flat-square&logo=postgresql" alt="PostgreSQL" />
  <img src="https://img.shields.io/badge/Redis-DC382D?style=flat-square&logo=redis" alt="Redis" />
  <img src="https://img.shields.io/badge/Cloudflare-Pages-F38020?style=flat-square&logo=cloudflare" alt="Cloudflare Pages" />
  <img src="https://img.shields.io/badge/PydanticAI-7C3AED?style=flat-square" alt="PydanticAI" />
</p>

---

## Features

### Scheduling & waiting room

- Appointment lifecycle: Scheduled, Confirmed, Cancelled, No Show, Rescheduled
- Day-of visit status: Arrived, In Consultation, Completed
- Drag-and-drop calendar, walk-ins, recurring series, and **double-booking prevention** (Postgres `btree_gist` exclusion constraint)
- Public self-service booking link (`/book/:clinicSlug`)
- **Live waiting room** with WebSocket updates, doctor filters, and kanban board
- Mobile shell with bottom tab bar (Calendar, Waiting, Patients, More) for front-desk tablets

### Patients & clinical records

- Patient registry with search, duplicate detection, and multi-doctor clinic scoping
- **Versioned SOAP notes** (Subjective, Objective, Assessment, Plan), vitals, diagnoses, specialty templates
- Prescriptions (e-Rx) with safety checks and PDF export
- Clinical orders, chart search (pgvector embeddings), consultation transcription
- Dental odontogram / tooth charting module
- Patient portal for visits, documents, and invoices

### Billing & documents

- Invoices, payments, credit notes, and membership plans
- PH payer workflows: eligibility, LOA, and insurance claims
- Document generation (certificates, referrals, receipts) from templates
- BIR compliance depth and printable PDFs (Rx, invoices, clinical documents)

### Communications & retention

- Appointment reminders and recall campaigns (email, SMS, WhatsApp adapters)
- In-app notification center for staff alerts
- NPS surveys and growth/retention tooling

### AI Clinic Assistant

- Chat panel that executes **real dashboard actions** (book, reschedule, draft SOAP, check balance, generate documents)
- **Tiered risk model** (Tier 0 read-only, Tier 1 auto-execute, Tier 2 confirm-required) computed server-side
- Clinical writes and patient messages always require human confirm
- Full audit trail via append-only `activity_log`
- AI SOAP draft (SSE streaming), billing extraction assist, and patient-facing FAQ assistant

### Platform & operations

- JWT auth with clinic-scoped roles: `owner`, `admin`, `doctor`, `reception`
- Multi-clinic **organizations** with workspace switcher
- Platform super-admin console (tenants, flags, metrics)
- Reports, analytics, and audit log UI
- Offline-resilient SOAP queue for degraded connectivity

---

## Screenshots

Portfolio images for this README live in [`docs/screenshots/`](./docs/screenshots/README.md). Capture them with the local stack running:

```bash
pnpm run capture:design-screenshots
```

Recommended captures: login, dashboard overview, appointment calendar, waiting room, patient chart, SOAP editor, billing invoice, and AI assistant panel.

---

## Tech Stack

| Layer             | Technology                                                                                                                                 |
| ----------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| Monorepo          | [pnpm](https://pnpm.io/) workspaces + [Turborepo](https://turbo.build/)                                                                    |
| Frontend          | [React 19](https://react.dev/) + [TanStack Start](https://tanstack.com/start) + [Vite](https://vite.dev/) + TypeScript                     |
| Routing / data    | [TanStack Router](https://tanstack.com/router), [TanStack Query](https://tanstack.com/query), [TanStack Table](https://tanstack.com/table) |
| Forms             | React Hook Form + [Zod](https://zod.dev/)                                                                                                  |
| UI                | [Tailwind CSS](https://tailwindcss.com/) + [shadcn/ui](https://ui.shadcn.com/)                                                             |
| **Backend**       | [FastAPI](https://fastapi.tiangolo.com/) (Python). Owns all business logic                                                                 |
| ORM / migrations  | [SQLAlchemy 2](https://www.sqlalchemy.org/) (async) + [Alembic](https://alembic.sqlalchemy.org/)                                           |
| **Database**      | [PostgreSQL](https://www.postgresql.org/) ([Neon](https://neon.tech/)) + [pgvector](https://github.com/pgvector/pgvector)                  |
| Jobs / cache      | [Redis](https://redis.io/) + [ARQ](https://arq-docs.helpmanual.io/) on the API host                                                        |
| Realtime          | FastAPI WebSockets (`/ws/clinic/{id}`)                                                                                                     |
| Files             | [Cloudflare R2](https://www.cloudflare.com/products/r2/) (presigned URLs)                                                                  |
| **AI**            | [PydanticAI](https://ai.pydantic.dev/), OpenAI / Gemini APIs, faster-whisper transcription                                                 |
| API client        | [Orval](https://orval.dev/) (OpenAPI → TypeScript + TanStack Query hooks)                                                                  |
| **Web hosting**   | [Cloudflare Pages](https://pages.cloudflare.com/)                                                                                          |
| **API hosting**   | Hetzner VPS (uvicorn + ARQ worker + Redis)                                                                                                 |
| Email / messaging | Resend, Twilio SMS, Meta WhatsApp (optional, clinic opt-in)                                                                                |

Full rationale: [`docs/tech-stack.md`](./docs/tech-stack.md).

---

## Getting Started

### Prerequisites

- [Node.js](https://nodejs.org/) 20+ and [pnpm](https://pnpm.io/) 9+
- [uv](https://docs.astral.sh/uv/) (Python package manager for `apps/api`)
- [Docker](https://www.docker.com/) (local Postgres+pgvector, Redis, MinIO, Mailhog)

### 1. Clone and install

```bash
git clone https://github.com/sprmke/kame-desk.git
cd kame-desk
pnpm install
pnpm run setup:ai-tooling   # once, after clone; links Cursor/Claude/OpenCode skills
```

### 2. Environment variables

```bash
cp apps/api/.env.example apps/api/.env
```

Fill in at minimum for local dev (defaults in `.env.example work with Docker Compose):

| Variable       | Description                                    |
| -------------- | ---------------------------------------------- |
| `DATABASE_URL` | Async Postgres URL (local Docker or Neon)      |
| `REDIS_URL`    | Redis connection string                        |
| `SECRET_KEY`   | JWT signing secret (`openssl rand -hex 32`)    |
| `CORS_ORIGINS` | Web origin (`http://localhost:3100` for local) |
| `WEB_BASE_URL` | Public web URL for links in emails/reminders   |
| `S3_*`         | MinIO locally; Cloudflare R2 in deployed envs  |

Optional: LLM API keys for AI features, SMTP/Resend for outbound email, WhatsApp webhook token. See [`apps/api/.env.example`](./apps/api/.env.example) and [`docs/architecture/deployment.md`](./docs/architecture/deployment.md).

### 3. Python dependencies

```bash
cd apps/api && uv sync --all-extras
```

### 4. Local services & database

```bash
pnpm run dev:docker          # Postgres+pgvector, Redis, MinIO, Mailhog
pnpm run db:migrate          # Alembic upgrade head (local only)
pnpm run db:seed             # synthetic dev data (never real patient data)
```

### 5. Run locally

```bash
pnpm run dev                 # web :3100 + api :8100 + ARQ worker
```

Open [http://localhost:3100](http://localhost:3100). API health: [http://localhost:8100/api/v1/health](http://localhost:8100/api/v1/health).

---

## Scripts

| Command                               | Description                                            |
| ------------------------------------- | ------------------------------------------------------ |
| `pnpm run dev`                        | Web + API + worker together (`./dev.sh`)               |
| `pnpm run dev:web`                    | TanStack Start dev server only                         |
| `pnpm run dev:api`                    | FastAPI with reload only                               |
| `pnpm run dev:worker`                 | ARQ background worker only                             |
| `pnpm run dev:docker`                 | Start local Docker services                            |
| `pnpm run build`                      | Turborepo production build                             |
| `pnpm run lint`                       | ESLint + Ruff across the monorepo                      |
| `pnpm run type-check`                 | TypeScript + mypy checks                               |
| `pnpm run test`                       | Vitest (web) + pytest (api)                            |
| `pnpm run ci:quality`                 | Full CI gate (lint, type-check, build, test)           |
| `pnpm run db:migrate`                 | Apply Alembic migrations (local Postgres)              |
| `pnpm run db:migrate:new`             | Generate a new Alembic revision (review before commit) |
| `pnpm run db:seed`                    | Seed local dev database                                |
| `pnpm run db:reset:local`             | Drop, recreate, migrate, and seed local DB             |
| `pnpm run db:generate-client`         | Export OpenAPI + regenerate `packages/api-client`      |
| `pnpm run check:design-slop`          | Mechanical anti-slop ratchet                           |
| `pnpm run capture:design-screenshots` | Portfolio screenshots (needs local app)                |

Deploy scripts (`deploy:api:dev`, `deploy:web:prod`, etc.) are documented in [`docs/architecture/deployment.md`](./docs/architecture/deployment.md). Production deploys require explicit team approval.

---

## Project structure

```text
apps/
  web/                 # React + TanStack Start (UI only; no business logic)
  api/                 # FastAPI: routers, services, models, workers, AI
packages/
  api-client/          # Orval-generated TypeScript client + Query hooks
docs/
  mvp.md               # Authoritative product PRD
  tech-stack.md        # Authoritative technology choices
  architecture/        # Data model, API conventions, deployment, security
  phases/              # Multi-phase build plan (Phases 0–47)
  guides/routes/       # Per-route behavior specs
scripts/               # Dev helpers, deploy, design-slop checks
.agent/                # Canonical AI skills (symlinked into Cursor/Claude)
```

---

## Routes

| Route pattern               | Access         | Description                        |
| --------------------------- | -------------- | ---------------------------------- |
| `/login`, `/register`       | Public         | Clinic staff auth                  |
| `/onboarding`               | Auth           | Clinic setup wizard                |
| `/dashboard`                | Auth           | Today / overview                   |
| `/dashboard/appointments/*` | Auth           | List, calendar, new, SOAP          |
| `/dashboard/waiting-room`   | Auth           | Live visit queue                   |
| `/dashboard/patients/*`     | Auth           | Registry, chart, Rx, billing       |
| `/dashboard/billing/*`      | Auth           | Invoices, claims, LOA, eligibility |
| `/dashboard/settings/*`     | Auth           | Clinic, team, services, assistant  |
| `/book/:slug`               | Public         | Self-service booking               |
| `/patient-portal/:slug/*`   | Patient token  | Visits, documents, invoices        |
| `/platform/*`               | Platform admin | Tenant management                  |

Full route guide index: [`docs/guides/routes/README.md`](./docs/guides/routes/README.md).

---

## Documentation

| Doc                                                    | Purpose                                                                                  |
| ------------------------------------------------------ | ---------------------------------------------------------------------------------------- |
| [`docs/mvp.md`](./docs/mvp.md)                         | Authoritative product PRD: modules, AI assistant spec, production readiness checklist    |
| [`docs/tech-stack.md`](./docs/tech-stack.md)           | Authoritative technology choices                                                         |
| [`docs/architecture/`](./docs/architecture/)           | Monorepo structure, data model, API conventions, AI assistant spec, deployment, security |
| [`docs/phases/README.md`](./docs/phases/README.md)     | Multi-phase build plan: detailed tasks per phase, in build order                         |
| [`docs/guides/routes/`](./docs/guides/routes/)         | Per-page behavior, save paths, RBAC, and edge cases                                      |
| [`CLAUDE.md`](./CLAUDE.md)                             | Agent context (Claude Code, Cursor, OpenCode): stack, commands, conventions              |
| [`.cursor/rules/README.md`](./.cursor/rules/README.md) | Cursor rules and skills index                                                            |

**Current status:** Phases 0–43 shipped. Active work is the professional design overhaul (Phases 44–47). Tracker: [`docs/workflow/in-progress/professional-design-overhaul-anti-slop.md`](./docs/workflow/in-progress/professional-design-overhaul-anti-slop.md).

---

## Design

Operational software for a Philippine private clinic: calm, dense, divider-first layouts. Tokens and surfaces: [`docs/architecture/design-language.md`](./docs/architecture/design-language.md). Pass/fail rules: [`.cursor/rules/anti-slop-design.mdc`](./.cursor/rules/anti-slop-design.mdc).

---

## Related repos

| Repo           | Relationship                                                                                                        |
| -------------- | ------------------------------------------------------------------------------------------------------------------- |
| **kame-lends** | Sibling portfolio project (SvelteKit loan management). Shares AI-tooling and doc-sync patterns, not backend code.   |
| **kame-crew**  | Sibling portfolio project (Next.js AI companion app). Reference for README and portfolio presentation.              |
| **kame-homes** | Separate product (React + Supabase). AI dashboard assistant patterns informed DoctorDesk's Clinic Assistant design. |

---

<p align="center">
  Built for clinics that need one system for the front desk, the consult room, and the books, with an assistant that does the clicking when staff are busy.
</p>
