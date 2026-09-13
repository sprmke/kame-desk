# Phase 37: Patient self-service portal

**Status:** Done
**Depends on:** Phase 24, Phase 21
**Unlocks:** —

**Plan reference:** `docs/workflow/planned/clinic-software-market-research-feature-gaps.md` §4.2 #2

## Production defaults (resolves plan §5 open decision 1)

- Pulled forward from "deferred" per the user's decision to implement the full research backlog. Scope stays intentionally narrow versus the international 99%-adoption pattern: view own chart summary (diagnoses, visit history, vitals trend), past visit list, invoices/balance, and document downloads. No messaging-to-doctor, no self-edit of clinical data, no lab-result upload — those stay out of scope to avoid the auth/consent surface the original MVP reasoning flagged.
- **Correction to this phase doc's original premise:** there is no existing "public booking-link identity model" to reuse — the public booking flow (`mvp.md` §7.3) is fully anonymous phone/email matching with no token, no verification, and no session. Patient auth for the portal is genuinely new. It is modeled instead on the staff `AccountToken` / `account_service.py` pattern already in this repo (hashed, single-use, expiring token row), which is the right level of rigor for PHI access — the weaker `Reminder.reply_token` pattern (no expiry, no single-use) used for confirm/cancel taps was rejected as insufficient for this surface.
- Auth design: a new `PatientPortalToken` table (`patient_id` + `clinic_id`, hashed token, 15-minute TTL, single-use) issued by `POST /patient-portal/login/request` and delivered as a magic link only (no separate numeric-OTP UX, to keep the surface small) via whichever of email/SMS matches what's on file — SMS reuses the clinic's own Twilio credentials exactly like reminders do, so a clinic with no SMS provider configured falls back to email-only. The request endpoint always returns the same generic response regardless of whether the identifier matched, to avoid confirming/denying a phone or email is a patient of the clinic. `POST /patient-portal/login/verify` exchanges the one-time link token for a short-lived `patient_access` JWT (30 min), a new token `type` alongside `access`/`refresh`, with `sub` = patient id and `clinic_id` baked into the claims at issuance (portal sessions are single-clinic, matching the data model — a `Patient` row belongs to exactly one clinic). A new `get_current_patient` FastAPI dependency in `core/security.py` verifies it, mirroring `get_current_user` but without any `X-Clinic-Id` header trust or runtime clinic switching.
- Chart summary intentionally does not expose raw SOAP `subjective` / `objective` / `plan` text to the patient — only `diagnosis_primary`, `diagnosis_secondary`, `icd10_codes`, and `follow_up_date` per visit, plus the `PatientVital` history for trend charts. This keeps the "no self-edit, no raw chart" boundary from leaking into "no read access to the clinical narrative either," which the phase's own edge cases don't ask for.

## Goal

A patient can log into a portal, see their own visit history, chart summary, invoices, and download their documents, without staff involvement.

## Tasks

### Backend

- [x] Patient auth: magic-link login scoped to the requesting patient's own `patient_id`, no password, short-lived tokens (`PatientPortalToken`, modeled on `account_token.py`)
- [x] Read-only endpoints: `GET /patient-portal/me`, `/visits`, `/chart-summary`, `/invoices`, `/documents` — all scoped server-side to the authenticated patient via `get_current_patient`, never trust a client-supplied `patient_id`
- [x] Document download endpoint reuses existing R2 signed-URL pattern from Phase 10 (`storage_service.create_presigned_download`)
- [x] `activity_log`: `patient_portal.login`, `patient_portal.document_downloaded`

### Frontend

- [x] New patient-facing route group (`apps/web/src/routes/patient-portal.$slug.*.tsx`), fully separate from the clinic staff app shell, mobile-first
- [x] Login (request magic link) → visit history list → chart summary (not full raw SOAP) → invoices/balance → documents
- [x] Explicit consent/privacy notice on first login (PHI exposure to the patient's own device), acknowledged once per browser

## Edge cases

- Patient has records across multiple clinics on kame-desk → portal is clinic-scoped per login (matches existing booking-link model), not a cross-clinic account
- Guardian/minor patient access → out of scope for MVP; portal login requires the patient's own verified contact info on file, no proxy-access model yet (flag as an open question if it comes up in pilot)
- Patient revokes/loses access to their phone/email on file → staff can regenerate contact info from the existing patient-record flow, same as today

## Bugs found during live-browser verification (fixed before marking Done)

- The magic-link URL built by `request_login_link` was missing the `/{clinic.slug}/` path segment (`/patient-portal/verify?token=...` instead of `/patient-portal/{slug}/verify?token=...`), which would have 404'd for every real patient. Caught by reading the actual email out of Mailhog in a live run, not by unit tests (the tests only asserted the token was extractable, not the URL shape) — fixed, and the tests now also assert the full path.
- Chart summary's `visit_date` used `SoapNote.created_at` (when the note was saved) instead of the appointment's `scheduled_start` (when the visit happened) — cosmetically correct in tests (same instant) but wrong for any real chart. Fixed by joining `Appointment` and ordering/reporting by `scheduled_start`.
- The patient-portal API client only cleared the stored token on a 401; it never redirected, so a logged-out patient hitting a bookmarked or shared protected URL directly (bypassing the router's client-side guard, which only runs on the SSR-to-hydration boundary) saw a blank authenticated-looking shell with failed requests instead of the login page. Fixed by adding the same hard `window.location.assign` redirect the staff `apiClient.ts` already uses for this exact case.
- Unrelated but blocking `pnpm run ci:quality`: accepting a doctor invitation double-counted the invitation being accepted as still "pending" while also about to become an active seat, so a starter-plan clinic's very first doctor invite could never be accepted. Fixed in `seat_service.py`/`clinic_service.py` (exclude the invitation being accepted from the pending count) with a regression test in `test_onboarding.py`.

## Docs to update

- `docs/mvp.md` §14 — remove patient portal from "Out of Scope," add to §6 as a real module
- `docs/architecture/security-compliance.md` — new auth tier (patient portal token)
- New `docs/guides/routes/patient-portal.md`

## Exit criteria

- [x] Patient can log in and see only their own data — verified in a live browser (real magic-link email via Mailhog, full visits/chart/invoices/documents flow, cross-clinic isolation test in `test_patient_portal.py`)
- [x] No staff-app code path is reachable from the patient-portal route group — separate route files, separate shell component, separate localStorage session key and API client
- [x] `pnpm run ci:quality` green (192 backend tests, 75 frontend tests, both type-checks, both lints)
