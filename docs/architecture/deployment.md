# Deployment

Standing reference for environments, infra, and release process. Real infra is provisioned in Phase 19 (`docs/phases/phase-19-hardening-production-readiness.md`) — until then, this doc describes the target state and the local-dev equivalent every earlier phase actually runs against.

## Environments

| Environment     | Web                                                | API                                       | Database                         | Files                       | Purpose                                                           |
| --------------- | -------------------------------------------------- | ----------------------------------------- | -------------------------------- | --------------------------- | ----------------------------------------------------------------- |
| **Local dev**   | Vite dev server                                    | `uv run uvicorn --reload`                 | Docker Compose Postgres+pgvector | MinIO (R2 stand-in)         | Day-to-day development (Phases 1–18)                              |
| **Dev/staging** | Cloudflare Pages (preview or dedicated dev domain) | Hetzner VPS (dev) or a smaller shared box | Neon (dev branch)                | Cloudflare R2 (dev bucket)  | Pre-pilot integration testing (introduced when Phase 19 needs it) |
| **Production**  | Cloudflare Pages                                   | Hetzner VPS (CX22)                        | Neon (prod)                      | Cloudflare R2 (prod bucket) | Real pilot clinics, real patient data                             |

`pnpm run env:status` reports which environment the current `apps/api/.env` targets.

## Local development

```bash
pnpm install
pnpm run dev:docker   # Postgres+pgvector, Redis, MinIO, Mailhog
pnpm run dev          # web + api + worker together (./dev.sh)
```

### Local demo data

After migrations, load synthetic clinic data for UI review:

```bash
pnpm run db:seed              # skip if demo clinic already exists
pnpm run db:seed:force        # replace demo clinic only (local dev)
pnpm run db:reset:local       # drop DB, migrate, seed (clean slate)
```

All demo staff accounts use password `password123`. Seed covers every shipped module (patients, calendar, waiting room, SOAP, Rx, billing, claims, LOA, eligibility, documents, reminders, recalls, notifications, reports, audit log, waitlist, clinical orders, AI assistant, patient portal, organization, Super Admin).

**Makati Family Clinic** (`makati-family-clinic`, public booking `/book/makati-family-clinic`):

| Role                     | Email                   |
| ------------------------ | ----------------------- |
| Owner                    | `demo@example.com`      |
| Doctor                   | `dr.santos@example.com` |
| Reception                | `reception@example.com` |
| Admin                    | `admin@example.com`     |
| Admin (also Super Admin) | `platform@example.com`  |

**Makati Family Clinic BGC** (`makati-family-clinic-bgc`, `/book/makati-family-clinic-bgc`):

| Role              | Email                       |
| ----------------- | --------------------------- |
| Owner (same user) | `demo@example.com`          |
| Doctor            | `dr.reyes@example.com`      |
| Reception         | `reception.bgc@example.com` |
| Admin (same user) | `admin@example.com`         |

Organization: `Makati Family Group`. Owner and admin can switch clinics in the header. Super Admin (`/platform`) requires `PLATFORM_ADMIN_EMAILS=platform@example.com` in `apps/api/.env`. Patient portal: `/patient-portal/makati-family-clinic/login` (seed prints a verify link). Data is fictional. Never use real patient information in seeds.

Mailhog captures all outbound email locally (never sends real email in dev). MinIO stands in for Cloudflare R2 with an S3-compatible API — presigned URL logic is identical against both, only the endpoint/credentials differ per environment.

## Production topology

```
Cloudflare Pages (apps/web)
        │ HTTPS
        ▼
Hetzner VPS (CX22, always-on)
  ├─ uvicorn → FastAPI (REST /api/v1 + WebSockets + SSE)
  ├─ arq worker (transcription, embeddings, recurring expand, reminders)
  └─ Redis (same host)
        │
   ┌────┼────────────────┐
   ▼    ▼                ▼
Neon   Cloudflare R2   LLM APIs
Postgres (files/audio)  (OpenAI/Gemini)
+pgvector
```

Why always-on (not serverless): the live waiting room (Phase 5) needs persistent WebSocket connections, and background jobs (transcription, embeddings, recurring expansion) need a real worker process — a small fixed VPS is simpler and cheaper than polling or splitting workers across serverless for a single clinic's steady business-hours traffic. See `docs/tech-stack.md` § Why always-on.

## Deploy commands

Configure `scripts/deploy/.env.dev` / `.env.prod` from `scripts/deploy/.env.example` (SSH host, API path, Cloudflare Pages project, `VITE_API_URL`, `REMOTE_DATABASE_URL`).

```bash
pnpm run deploy:api:dev / deploy:web:dev     # requires scripts/deploy/.env.dev (see scripts/deploy/.env.example)
pnpm run deploy:api:prod / deploy:web:prod   # PRODUCTION — deskwave unlock + scripts/deploy/.env.prod
pnpm run migrate:prod                         # remote Alembic upgrade against prod Neon — deskwave required
pnpm run backup:db:dev / :prod                # pre-deploy backups (also automatic before deploy)
pnpm run rollback:db:dev / :prod              # restore most recent backup (prod: deskwave required)
```

**Production deploys and migrations require the unlock word `deskwave` in the same message/command**, per `.cursor/rules/no-prod-deploy.mdc` (created Phase 0). No agent runs or recommends a blocked production operation without it. This mirrors the `kamewave` pattern already proven in the sibling `kame-homes` repo.

## Migrations

Alembic only, against `apps/api/migrations/`. Local: `pnpm run db:migrate` (`alembic upgrade head`, local Postgres only). Never edit a shipped migration under `migrations/versions/` — add a new one. Remote (prod) migrations run via `pnpm run migrate:prod`, gated by the same `deskwave` unlock. Full authoring conventions: `.cursor/rules/migrations.mdc` (Phase 0).

Phase 21 adds `022_account_foundations` (`account_tokens`, `users.email_verified_at`, `clinics.deletion_requested_at`).

## Backups & restore

Automated daily backup against Neon (prod), taken automatically before every prod deploy in addition to the daily schedule. **A restore must be tested against a real snapshot at least once before the first pilot clinic goes live** (`mvp.md` §12).

### Restore runbook (local + prod)

| Step           | Command / action                                                                                     |
| -------------- | ---------------------------------------------------------------------------------------------------- |
| 1. Stop writes | Disable public booking if needed; use AI/platform kill switches for assistant features               |
| 2. Backup      | `pnpm run backup:db:dev` or `pnpm run backup:db:prod` (prod requires `deskwave` in the same message) |
| 3. Restore     | `pnpm run rollback:db:dev` or `pnpm run rollback:db:prod` (prod requires `deskwave`)                 |
| 4. Verify      | `pnpm run db:migrate` against restored DB; smoke-test auth + one appointment read                    |
| 5. Resume      | Re-enable traffic after clinic sign-off                                                              |

Local restore drill evidence: run `pnpm run backup:db:dev` then `pnpm run rollback:db:dev` in CI or before pilot. Prod restore drill is a manual gate before first real clinic (requires `deskwave`).

## Phase 19 production-readiness evidence

| Checklist area                          | Evidence in repo                                                                                                                                                                                   |
| --------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Full regression                         | `pnpm run ci:quality` (pytest + Vitest + type-check + lint + build)                                                                                                                                |
| Patient lifecycle (API)                 | `apps/api/tests/test_patient_lifecycle.py`                                                                                                                                                         |
| Double-booking concurrency              | `apps/api/tests/test_calendar_public_booking.py::test_public_staff_booking_race`, `scripts/load/concurrent_booking.py`                                                                             |
| Tier 2 confirm / kill switch            | `apps/api/tests/test_assistant.py`                                                                                                                                                                 |
| Visit summary never auto-sends          | `apps/api/tests/test_phase18.py::test_visit_summary_requires_approval`                                                                                                                             |
| Patient assistant grounding             | `apps/api/tests/test_phase18.py`, `apps/web/src/features/booking/lib/groundingFacts.test.ts`                                                                                                       |
| No-show risk heuristic                  | `apps/api/tests/test_no_show_risk.py`                                                                                                                                                              |
| RBAC spot-check                         | `apps/api/tests/test_security_rbac.py`, `test_soap.py` (reception SOAP), `test_prescriptions.py`                                                                                                   |
| Patient intake consent                  | Migration `020_hardening`, `PatientNewPage` checkbox, `test_security_rbac.py::test_patient_create_requires_consent_*`                                                                              |
| Public assistant tool injection         | Production ignores `__tool__:` payloads; natural-language booking uses the LLM planner. Tests may inject `__tool__:` only when `DOCTORDESK_TESTING=1` (`test_security_rbac.py`, `test_phase18.py`) |
| Chart immutability                      | `apps/api/tests/test_soap*.py` (versioned writes)                                                                                                                                                  |
| PWA manifest + SW                       | `apps/web/public/manifest.webmanifest`, `apps/web/public/sw.js` (SW off in Vite dev)                                                                                                               |
| Staff Web Push (optional)               | API: `VAPID_PUBLIC_KEY`, `VAPID_PRIVATE_KEY`, `VAPID_SUBJECT`; Web: `VITE_VAPID_PUBLIC_KEY`. Push fanout no-ops when unset.                                                                        |
| Command palette                         | `apps/web/src/components/CommandPalette.tsx` (Cmd/Ctrl+K)                                                                                                                                          |
| E2E (onboarding + patients + assistant) | `apps/web/e2e/*.spec.ts` via `scripts/ci/e2e.sh` (CI `e2e` job)                                                                                                                                    |
| Local backup                            | `pnpm run backup:db:dev` (`scripts/deploy/backup-db.sh`; Docker Compose `pg_dump` fallback when host tools missing)                                                                                |
| Deploy scripts                          | `scripts/deploy/deploy-api.sh` (rsync + SSH + migrate + systemd), `deploy-web.sh` (build + wrangler pages); template `scripts/deploy/.env.example`                                                 |
| Prod deploy                             | **Manual** — provision infra, copy `.env.prod`, run with `deskwave` unlock (not run in agent sessions by default)                                                                                  |

## Monitoring & incident response

- Error tracking: Sentry, both `apps/web` and `apps/api`, PHI-scrubbed (see `docs/architecture/security-compliance.md`)
- Uptime monitoring configured before pilot launch (Phase 19), target ≥99.5% during business hours (Asia/Manila), per `mvp.md` §4
- **Pilot support channel:** `support@doctordesk.app` (replace with the live inbox before first clinic). Escalation: on-call engineer via the team's incident channel.
- **Incident plan (data-affecting bug):**
  1. Stop writes: disable public booking, flip platform/clinic AI kill switches, post maintenance notice if needed.
  2. Snapshot: `pnpm run backup:db:prod` (requires `deskwave` in the same message).
  3. Restore: `pnpm run rollback:db:prod` only after root cause is understood and clinic owners are notified.
  4. Verify: `pnpm run db:migrate`, smoke auth + appointment read, replay failed mutations from `activity_log` if required.
  5. Resume traffic after clinic sign-off.

## Load testing

- Automated concurrent booking probe: `scripts/load/concurrent_booking.py` (run against local or dev API with a valid JWT).
- Pytest race coverage: `test_concurrent_double_booking`, `test_public_staff_booking_race`.

## CI

`.github/workflows/ci.yml`: `quality` job runs `pnpm run ci:quality` (lint, type-check, build, pytest, Vitest). `e2e` job runs `scripts/ci/e2e.sh` (Playwright against preview web + API with Postgres + Redis services). Local E2E: `pnpm run dev:docker` then `pnpm run test:e2e`.

## Estimated infra cost (early stage)

| Service          | Role                | Est. cost    |
| ---------------- | ------------------- | ------------ |
| Hetzner CX22     | API + ARQ + Redis   | €4–6/mo      |
| Neon             | Postgres + pgvector | $0 free tier |
| Cloudflare Pages | Web app             | $0           |
| Cloudflare R2    | Files               | $0 free tier |
| Resend           | Email               | $0 free tier |
| Sentry           | Errors              | $0 free tier |

**MVP infra: about $5–15/month before LLM and SMS usage.** LLM (OpenAI/Gemini) and Twilio SMS usually cost more than hosting — see `docs/tech-stack.md` § AI for cap/meter strategy.
