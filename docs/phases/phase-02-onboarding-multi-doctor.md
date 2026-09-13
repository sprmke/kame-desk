# Phase 2: Clinic onboarding wizard + multi-doctor support

**Status:** Done
**Depends on:** Phase 1
**Unlocks:** Phase 3

**mvp.md reference:** §6.1, §7.1, §7.2 · Gap closed: #1 and #2 in §7

## Goal

A brand-new clinic owner who just registered (Phase 1) lands on a guided setup wizard instead of an empty dashboard, and by the end of it the clinic has a complete profile, at least one doctor, working hours, fees, and (optionally) invited staff. This phase also builds out true multi-doctor support: a clinic can have 2+ doctors sharing one front desk and one patient registry, each with their own calendar.

## Prerequisites

- Phase 1 done: auth, `clinics`/`users`/`clinic_memberships` tables, RBAC dependency working

## Tasks

### 1. Database

- [x] Extend `clinics`: license/accreditation info, logo_url (R2 key), working_hours (jsonb per day), holiday_dates (array or separate `clinic_holidays` table), default_appointment_duration_minutes
- [x] `doctor_profiles` table — user_id, clinic_id, specialty, prc_license_number, signature_image_url (R2 key), photo_url, consultation_fee, follow_up_fee, default_appointment_duration_minutes (overrides clinic default)
- [x] `service_fees` table — clinic_id, name, amount, category (used later by billing, Phase 9, but the fee list is configured here)
- [x] `staff_invitations` table — clinic_id, email, role, invited_by_user_id, token, expires_at, accepted_at, revoked_at
- [x] Alembic migrations for all of the above

### 2. Backend

- [x] `PATCH /api/v1/clinics/{clinic_id}` — update clinic profile (owner/admin only)
- [x] `PUT /api/v1/clinics/{clinic_id}/working-hours` — per-day hours + holidays
- [x] `POST /api/v1/clinics/{clinic_id}/doctors` — create a doctor profile for an existing or newly-invited user
- [x] `PATCH /api/v1/doctors/{doctor_id}` — update specialty/fees/signature
- [x] `POST /api/v1/doctors/{doctor_id}/signature-upload` — presigned R2 upload for signature image
- [x] `GET/POST/PATCH/DELETE /api/v1/clinics/{clinic_id}/service-fees`
- [x] `POST /api/v1/clinics/{clinic_id}/invitations` — creates a `staff_invitations` row, sends an email (Resend) with an accept link + token
- [x] `POST /api/v1/invitations/{token}/accept` — creates `clinic_memberships` row for the invited role; if the invited user doesn't have an account yet, this endpoint doubles as the account-creation path (set password, then join)
- [x] `DELETE /api/v1/clinics/{clinic_id}/invitations/{invitation_id}` — revoke a not-yet-accepted invite (Tier 1 candidate later for the AI assistant, per mvp.md §9.5)
- [x] `GET /api/v1/clinics/{clinic_id}/onboarding-status` — returns which wizard steps are complete, so the frontend can resume a half-finished wizard on reload

### 3. Frontend

- [x] `src/features/onboarding/` — wizard shell with steps: Clinic profile → Doctor profile → Working hours → Fees → Invite staff → Done
- [x] Wizard persists progress server-side (via `onboarding-status`), not just in local component state — a refresh mid-wizard must not lose progress
- [x] Clinic switcher in the top nav (for users with 2+ clinic memberships) — needed once multi-doctor/multi-clinic is real
- [x] Staff management page (`src/features/settings/team/`) — list members, invite, change role, deactivate
- [x] Doctor profile page — specialty, PRC license, signature upload (used later by Rx/certs, Phase 8/10), fee overrides

## Data model

New: `doctor_profiles`, `service_fees`, `staff_invitations`, `clinic_holidays` (or jsonb column). Extended: `clinics`.

## API endpoints

See Backend tasks above for the full list. All require `require_clinic_role("owner", "admin")` except `GET onboarding-status` (any clinic member) and the public `POST /invitations/{token}/accept`.

## Edge cases & safety

- Inviting an email that's already a member of the clinic → 409, not a silent duplicate row.
- An expired or revoked invitation token must fail acceptance with a clear (non-leaky) error.
- Removing the last `owner` from a clinic must be blocked — every clinic needs at least one owner at all times.
- A doctor profile requires a linked `users` row with role `doctor` in `clinic_memberships` — creating one without the other is an invalid state; wrap in a DB transaction.
- Working hours changes must not retroactively invalidate already-booked appointments outside the new hours — Phase 3+ scheduling logic checks hours only for _new_ bookings; flag (don't auto-cancel) existing ones that now fall outside hours.
- Signature/photo uploads: validate file type/size before issuing a presigned URL; R2 objects are never public (see `docs/architecture/security-compliance.md`).

## Testing

- pytest: full onboarding flow (register → complete wizard → verify `onboarding-status` returns all-complete); invite → accept → new membership; last-owner-removal guard
- Vitest: wizard step validation, resume-on-reload behavior
- Playwright (first E2E spec in the repo): register → onboarding wizard happy path

## Docs to update in this phase

- `docs/guides/routes/dashboard/settings/` (or equivalent) — onboarding wizard + team management pages, per `route-guides.mdc`
- `docs/architecture/data-model.md` — new tables
- `mvp.md` §15 open question #7 (pilot clinic data import) — note if this phase surfaces a need for import tooling, otherwise leave as an open question

## Exit criteria

- [x] A brand-new clinic can complete onboarding with zero engineering support (first line item of `mvp.md` §12 Production Readiness Checklist)
- [x] A clinic can have 2+ doctors, each with their own profile/fees, sharing one front desk login set
- [x] Staff invitation → acceptance → correct role assigned, end to end
- [x] `pnpm run ci:quality` green, Playwright onboarding spec passing
