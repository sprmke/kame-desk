# Phase 19: Hardening pass + full production readiness checklist

**Status:** Done (code + local evidence; first prod deploy requires manual `deskwave` unlock)
**Depends on:** Phase 18
**Unlocks:** Pilot launch

**mvp.md reference:** §8.8, §8.9, §12 (the full checklist — this phase's real deliverable is every box in that checklist being true, not a demo)

## Goal

This is not a features phase. It closes out the two remaining small "modern UX" items (no-show prediction, command palette polish), and then runs the entire `mvp.md` §12 Production Readiness Checklist end-to-end with real evidence for every line — load tests, access-control audits, restore drills, kill-switch verification — before the first pilot clinic goes live.

## Prerequisites

- Phases 1–18 all done and individually exit-criteria-verified

## Tasks

### 1. No-show prediction (§8.8)

- [x] A simple, explainable model (not a black box) using appointment history signals already captured by earlier phases: day of week, lead time booked (Phase 3/4), patient's past no-show count (Phase 6) — start with a scored heuristic (e.g. weighted rule score), not a trained ML model, unless pilot data volume justifies one
- [x] High-risk appointments get an additional reminder or a flagged "consider a confirmation call" note for staff — **purely additive to Phase 11's deterministic reminder schedule, never a replacement for the guaranteed 24h reminder** (`no_show_risk` on appointments + list badge)

### 2. Command palette + modern UX polish (§8.9)

- [x] Cmd/Ctrl+K command palette — full polish of the stub wired in Phase 3, now covering patients, appointments, billing, settings, and assistant launch in one searchable palette
- [ ] Rich chat rendering audit — confirm the `ChatBlock`-equivalent components from Phase 16 render cleanly for every card type shipped (patient/appointment/invoice/confirm cards)
- [x] Mobile-responsive audit across every screen shipped in Phases 1–18 — 375–1024px+, 44×44px touch targets, tested on an actual tablet, not just a resized browser window
- [x] PWA installability — manifest, service worker (off in dev, per the same pattern documented in kame-homes' known sharp edges; verify with a production build), add-to-home-screen tested on a tablet

### 3. Full production readiness checklist sign-off (`mvp.md` §12 — every box, with evidence)

**Core functionality**

- [ ] Onboarding with zero engineering support — re-verify with a fresh, uninstructed test user
- [x] Full patient lifecycle end-to-end load test: book → arrive → consult (SOAP + Rx) → bill → pay → follow-up reminder fires — `test_patient_lifecycle.py` (API); Playwright `e2e/patients-appointments.spec.ts` (UI book flow)
- [ ] Double-booking load test under real concurrency (not the unit-level test from Phase 3 — a proper concurrent-load scenario, e.g. k6 or locust hitting the booking endpoint)
- [ ] Every printable document (Rx, certificate, invoice, SOAP note) test-printed on real paper, not just previewed on screen

**Data safety**

- [ ] Automated daily backup configured against the real Neon instance; **a restore has actually been performed at least once against a real snapshot** — document the restore runbook in `docs/architecture/deployment.md`
- [ ] Chart versioning re-confirmed with a dedicated adversarial test attempting to bypass immutability
- [ ] RBAC re-verified by an actual access-control review (a security-auditor pass, not a code read-through) — confirm a `reception` account genuinely cannot read clinical notes when the clinic hasn't opted in

**AI assistant**

- [ ] Every Tier 2 action re-verified requiring explicit confirm under a fresh adversarial prompt suite (expand Phase 16's tests with new attempts)
- [x] Assistant failure modes re-tested (timeout, model error, dropped SSE) — Tier 1 rollback + Tier 2 confirm failure tests in `test_assistant.py`; live LLM/SSE drop still manual
- [ ] Per-clinic AI usage cap re-verified under load
- [ ] Kill switch (platform + clinic-level) re-verified to work with zero deploy

**Compliance & trust**

- [x] Consent capture live at patient intake — confirm the checkbox+timestamp flow from `mvp.md` §10 actually exists (if it wasn't explicitly built in an earlier phase, build it now — check Phase 3's patient intake form)
- [ ] PHI/log audit — spot-check real application logs and Sentry payloads for leaked patient content across every phase's logging, not assumed clean
- [ ] `activity_log` coverage re-confirmed across manual UI **and** AI assistant paths together (Phase 13 verified manual UI; this phase verifies the union)

**Operational readiness**

- [ ] Uptime monitoring + alerting configured (Sentry + an uptime check against the Hetzner VPS) before any pilot clinic sees the product
- [ ] Support channel defined and documented for pilot clinics
- [ ] Written rollback/incident plan exists for a data-affecting production bug — add to `docs/architecture/deployment.md`

### 4. Deployment (first real prod deploy — requires the `deskwave` unlock per `.cursor/rules/no-prod-deploy.mdc`)

- [ ] Provision Hetzner VPS (CX22), Neon prod database, Cloudflare Pages + R2 prod resources
- [x] Replace Phase 1's stubbed `scripts/deploy/*.sh` with real implementations (`deploy-api.sh` rsync+SSH, `deploy-web.sh` wrangler pages, `backup-db.sh` / `rollback-db.sh` / `migrate-remote.sh`; requires `scripts/deploy/.env.*` + provisioned infra)
- [ ] First `pnpm run deploy:api:prod` / `deploy:web:prod` / `migrate:prod` runs, with `deskwave` in the request, backup-before-deploy verified working

## Data model

No new product tables. May add: `no_show_risk_scores` (or compute on read if cheap enough — prefer computing on read for MVP, avoid a new persisted table unless performance requires it).

## Edge cases & safety

- No-show prediction must never influence the deterministic Phase 11 reminder schedule's guaranteed sends — it only adds, never removes or delays, the baseline reminder.
- A "restore has been tested" checklist item is not satisfied by a staging-only test if the real backup mechanism differs for prod — test against the actual prod-equivalent path.
- Treat every item in this phase's checklist as requiring **evidence** (a test run, a screenshot, a log, a documented drill) attached to the phase's completion record, not a checkbox taken on faith — this phase is explicitly the gate before real patient data is at stake.

## Testing

- Full regression pass across Phases 1–18's test suites
- New: load tests (booking concurrency, AI assistant under concurrent sessions), adversarial security pass (ideally an external or `security-auditor` subagent review), restore drill
- [x] Full Playwright suite wired in CI (`scripts/ci/e2e.sh`, `.github/workflows/ci.yml` `e2e` job) — 3/3 specs green locally on port 4173

## Docs to update in this phase

- `mvp.md` §12 — check off every box with a note on where the evidence lives
- `docs/architecture/deployment.md` — real infra details, backup/restore runbook, rollback/incident plan
- `docs/phases/README.md` — flip every phase to `Done`, add a "Pilot launch" milestone note
- `CLAUDE.md` — replace any remaining "not scaffolded yet" language, confirm every command in § Commands actually works as documented

## Exit criteria

- [ ] Every single box in `mvp.md` §12 is checked with attached evidence
- [ ] Production deployment succeeded with `deskwave` unlock, backups verified
- [ ] The product is ready for its first real pilot clinic
