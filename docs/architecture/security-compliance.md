# Security & compliance

Standing reference for the security/compliance invariants this product commits to. See `docs/mvp.md` §10 (Non-Functional Requirements) for the authoritative source; this doc is the implementation-facing companion, updated as each phase lands real enforcement.

## RBAC — server-side, always re-checked

The permission matrix is `mvp.md` §6.11:

| Role      | Scheduling          | Patient demographics | Clinical notes (SOAP)                                                | Prescriptions       | Billing         | Clinic settings |
| --------- | ------------------- | -------------------- | -------------------------------------------------------------------- | ------------------- | --------------- | --------------- |
| Owner     | Full                | Full                 | Full (own clinic)                                                    | Full                | Full            | Full            |
| Admin     | Full                | Full                 | View only                                                            | View only           | Full            | Full            |
| Doctor    | Full (own calendar) | Full                 | Full (own patients)                                                  | Full (own patients) | View own visits | None            |
| Reception | Full                | Full                 | **No access** by default (clinic-configurable to allow limited view) | No access           | Full            | None            |

**Non-negotiable:** enforced server-side on every endpoint via the `require_clinic_role(*roles)` FastAPI dependency (`docs/architecture/api-conventions.md`), never assumed from the UI hiding a button and never assumed from a DB constraint alone. Verified by an actual access-control review before pilot launch (`mvp.md` §12, owned by Phase 19), not a code read-through.

Never trust a client-supplied `clinic_id`. Never trust a model-asserted identity or record ID from an AI tool call (`docs/architecture/ai-clinic-assistant.md` § Safety model) — every tool re-derives and re-checks permissions the same way a direct API call would.

### Navigation permissions (UX layer)

Canonical strings live in `apps/api/app/core/permissions.py` and are returned on `GET /auth/me` when `X-Clinic-Id` is set. The web sidebar shows eight work destinations (Today, Schedule, Waiting room, Patients, Billing, Outreach, Documents, Insights) filtered by these permissions; Settings is a separate area reached from the header, not the main nav.

| Role      | Main nav                  | Settings                                                                          |
| --------- | ------------------------- | --------------------------------------------------------------------------------- |
| Owner     | All eight                 | All groups                                                                        |
| Admin     | All eight                 | All except clinic deletion                                                        |
| Doctor    | No Outreach               | Account, Doctor profile                                                           |
| Reception | No Documents, no Insights | Account only; Chart search under Patients when clinic enables reception SOAP view |

Hidden items, not disabled. Plan doctor seat limits (`starter` 1, `pro` 5, `clinic` unlimited) are enforced on doctor invites and accept via `app/services/seat_service.py`.

## Patient portal auth tier (Phase 37)

A fourth auth tier, distinct from clinic-user JWTs and the public/guest booking flow (`docs/mvp.md` §6.14 / §7.3):

| Tier           | Gate                                                         | Notes                                                                                                                            |
| -------------- | ------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------- |
| Patient portal | `patient_access` JWT (30 min), issued after a magic-link tap | `sub` is the patient id, `clinic_id` is baked into the claims at issuance — no `X-Clinic-Id` header, no runtime clinic switching |

- Login is a `PatientPortalToken` (hashed, single-use, 15-minute TTL) sent as a magic link, modeled on the staff `AccountToken` / `account_service.py` pattern — not the weaker `Reminder.reply_token` pattern (no expiry, no single-use), which stays appropriate only for low-stakes confirm/cancel replies, never PHI access.
- `POST /patient-portal/login/request` always returns the same generic response whether or not the identifier matched a patient, so it can't be used to enumerate who's a patient of a clinic.
- `get_current_patient` (`app/core/security.py`) verifies the JWT `type` is `patient_access`, loads the `Patient` row, and re-checks `clinic_id` matches the token's claim and the patient isn't archived — mirrors `get_current_user`/`get_active_clinic_membership`'s shape but is deliberately simpler (single-clinic, no membership table).
- Endpoints under `/patient-portal/*` (other than `login/request` and `login/verify`) are read-only and scoped to `get_current_patient`'s own `patient_id` — a patient can never pass another patient's id.
- The chart-summary endpoint never returns raw SOAP `subjective`/`objective`/`plan` text — only `diagnosis_primary`, `diagnosis_secondary`, `icd10_codes`, `follow_up_date`, and vitals history.
- Frontend: a fully separate route tree (`apps/web/src/routes/patient-portal.*`) and `PatientPortalAppShell`, with its own localStorage token key — no shared code path with `DashboardShell` or staff `isAuthenticated()`.

## PHI/PII handling

DoctorDesk stores Personal Health Information (patient medical records, vitals, prescriptions, SOAP notes, consultation audio) and PII (contact info, insurance details). Rules, applied from Phase 3 onward:

- **Never log patient content in plaintext.** Application logs and structured logs contain IDs and event types, never clinical text, contact info, or file contents.
- **Never send PHI to Sentry payloads.** Error tracking is PHI-scrubbed on both `apps/web` and `apps/api` — configure Sentry's `beforeSend` to strip known PHI-bearing fields, and review new endpoints for accidental inclusion in exception context.
- **Minimize what reaches an AI prompt/tool call.** See `docs/architecture/ai-clinic-assistant.md` § Prompt context minimization — a tool call receives only the fields it strictly needs, never a patient's full history by default.
- **Files (labs, images, audio) are never public.** Cloudflare R2 objects are accessed only via short-lived presigned URLs (Phase 3 for general files, Phase 15 for consultation audio) issued by FastAPI after an RBAC check — never a public bucket, never a long-lived link.

## Consent capture

Digital consent (checkbox + timestamp) for data storage and AI-assisted processing, captured at patient intake (`mvp.md` §10) — build this into Phase 3's patient intake form; do not defer it, since Phase 15's audio recording and Phase 14/16's AI features assume it already exists. E-signature capture is a nice-to-have, not required for v1.

**Consultation recording (Phase 15):** `clinics.recording_consent_enabled` must be true before `POST /appointments/{id}/recordings` is accepted. Raw audio is stored in private R2 only; presigned upload/download URLs expire in minutes. ARQ `purge_expired_recordings_job` deletes audio older than `RECORDING_RETENTION_DAYS` (default 90).

## Audit trail

`activity_log` (append-only, created Phase 1) is the single audit surface for both manual dashboard actions and AI-assistant-executed actions (`actor_type = 'user' | 'ai_assistant' | 'system'`). Every mutating endpoint writes here — Phase 13 runs a full sweep to confirm no gap exists across Phases 1–12, and Phase 16/19 extend that guarantee to AI-executed writes. The log itself is never editable or deletable through the app by any role, including owner. Phase 13 adds a Postgres `BEFORE UPDATE OR DELETE` trigger on `activity_log` as defense in depth, plus composite indexes on `(clinic_id, created_at)` and `(target_type, target_id)`.

## Data privacy compliance

Target market default: Philippine Data Privacy Act at minimum, with fields/consent capture designed so HIPAA-equivalent controls are not a rewrite later (`mvp.md` §10). `mvp.md` §15 open question #1 (confirm Philippines-first vs. market-agnostic defaults) should be resolved before Phase 9's receipt-numbering defaults (BIR OR format) are hardcoded anywhere beyond a configurable default.

## AI-specific safety boundaries

Full detail: `docs/architecture/ai-clinic-assistant.md`. Summary of the non-negotiables that are security/compliance-relevant specifically:

- AI output is always a draft a human confirms before anything clinical, financial, or patient-facing is persisted or sent — no exception, no "trusted user" bypass.
- Clinical writes (SOAP, prescriptions, diagnoses) and any real message sent to a patient are always Tier 2 (confirm-required), regardless of what a generic tier classifier would otherwise compute.
- Drug-interaction/allergy checks (Phase 8) are a deterministic rule/database check first; AI (Phase 17) only explains a flag in plain language, never decides whether to block.
- A per-clinic daily AI usage cap is enforced server-side before any model call, not just measured after the fact.
- **`drug_reference` (Phase 8, expanded Phase 25)** is a curated open list of common outpatient drugs. It catches obvious class conflicts (e.g. penicillin allergy vs amoxicillin). Drugs outside the list return `unchecked`. Not a substitute for a full drug database or pharmacist review.
- A platform-wide and a per-clinic kill switch can disable the AI assistant instantly, with no deploy needed.

## Transport & secrets

- HTTPS everywhere.
- JWT access (short-lived) + refresh (long-lived, rotated on use, revocable) tokens issued by FastAPI (Phase 1).
- Secrets: `apps/api/.env` (gitignored) locally; VPS environment or a secrets manager in production. Never committed, never logged.
- Third-party credentials that are themselves sensitive (Twilio SMS credentials, Phase 11) are stored encrypted at rest or via a secrets manager, never as plain readable columns.

## Production deploy guard

Production deploys, remote migrations, and any write against the prod Neon `DATABASE_URL` require the unlock word **`deskwave`** in the same request, enforced by shell hooks (`.cursor/rules/no-prod-deploy.mdc`, created Phase 0) in addition to this documented policy. See `docs/architecture/deployment.md`.

## Verification checklist (owned by Phase 19, tracked in full in `mvp.md` §12)

- [ ] RBAC verified by a real access-control review (not a read-through)
- [ ] No PHI present in logs or error-tracking payloads (spot-checked)
- [ ] Consent capture live at patient intake
- [ ] Audit log covers every mutating action across manual UI and AI assistant paths
- [ ] Every Tier 2 AI action requires explicit confirm, verified under adversarial prompt testing
- [ ] Kill switches (platform + per-clinic) verified functional with no deploy needed
- [ ] Automated backups running, restore tested at least once against a real snapshot
