# Phase 11: Reminders + recall campaigns

**Status:** Done
**Depends on:** Phase 10
**Unlocks:** Phase 12

**mvp.md reference:** §6.9, §7.6, §7.7 · Gap closed: #6 and #7 in §7 · biggest lever on the no-show-rate success metric (§4)

## Goal

Automated appointment confirmations and reminders (booking-time, 24h before, optional 2h before), reschedule/cancellation notifications, and recall campaigns driven by SOAP follow-up dates (Phase 7) and chronic-condition rules — via email (always available) and SMS (Twilio, clinic opt-in, metered).

## Prerequisites

- Phase 10 done. Requires Phase 6's ARQ worker pattern (recurring expansion) as a model for scheduled background jobs, and Phase 7's `follow_up_date` field to exist and be populated.

## Tasks

### 1. Database

- [x] `reminders` table (per tech-stack.md core data model addition) — id, appointment_id, clinic_id, patient_id, channel (`email`/`sms`), type (`confirmation`/`reminder_24h`/`reminder_2h`/`reschedule_notice`/`cancellation_notice`), scheduled_send_at, sent_at (nullable), status (`pending`/`sent`/`failed`/`cancelled`), provider_message_id (nullable)
- [x] `patient_recalls` table — id, clinic_id, patient_id, source (`follow_up_date`/`chronic_condition_rule`), due_date, status (`pending`/`contacted`/`booked`/`dismissed`), source_soap_note_id (nullable), created_at
- [x] `clinics.notification_preferences` (jsonb) — which reminders are on, lead time, SMS opt-in flag, sender identity
- [x] `clinics.twilio_credentials` (encrypted at rest, or referenced via a secrets manager — never store raw API keys in a plain jsonb column readable by a general query)

### 2. Backend

- [x] ARQ scheduled job: `dispatch_due_reminders` — runs on a short interval (e.g. every 5 minutes), finds `reminders` rows due to send, sends via Resend (email) or Twilio (SMS, only if clinic opted in and has credentials), updates status
- [x] Reminder creation is a **side effect of appointment creation/rescheduling/cancellation**, done inside the same service function (per `CLAUDE.md`'s "no duplicate side-effect logic" rule) — booking an appointment enqueues confirmation + 24h + optional 2h reminders in one transaction; rescheduling cancels the old pending reminders and creates new ones; cancelling cancels all pending reminders and sends a cancellation notice
- [x] ARQ scheduled job: `generate_recalls_from_follow_ups` — daily job that scans SOAP notes with a `follow_up_date` in the near future/past-due-and-unbooked and creates/updates `patient_recalls` rows
- [x] Chronic-condition recall rules (§7.7) — MVP scope: a simple clinic-configurable rule ("patients with condition X get a recall reminder every N months") rather than a complex rules engine; store as a small structured config, not free text
- [x] Two-way reply handling: patient replies to confirm/cancel/reschedule via a link in the email/SMS (not full inbound SMS parsing for MVP — a tokenized link is simpler and safer) → `POST /api/v1/public/reminders/{token}/respond`
- [x] `GET /api/v1/clinics/{id}/recalls` — pending recall list for staff to work from
- [x] `PATCH /api/v1/recalls/{id}` — mark contacted/booked/dismissed

### 3. Frontend

- [x] `src/features/settings/notifications/` — reminder lead-time config, SMS opt-in + Twilio credential entry, sender identity
- [x] `src/features/recalls/` — pending recalls list/board, one-click "book follow-up" action that pre-fills a new appointment for that patient
- [x] Dashboard "pending follow-ups" widget (§6.2) wired to `patient_recalls`
- [x] Public reply page (`/reminders/{token}`) — simple confirm/cancel/reschedule-request UI, no login

## Data model

New: `reminders`, `patient_recalls`. Extended: `clinics` (notification prefs, Twilio credentials).

## API endpoints

| Method    | Path                                            | Auth                    |
| --------- | ----------------------------------------------- | ----------------------- |
| GET/PATCH | `/api/v1/clinics/{id}/recalls`                  | owner, admin, reception |
| POST      | `/api/v1/public/reminders/{token}/respond`      | none (token-scoped)     |
| PATCH     | `/api/v1/clinics/{id}/notification-preferences` | owner, admin            |

## Edge cases & safety

- SMS is metered and clinic-opt-in per `tech-stack.md` — never send SMS for a clinic without valid, verified opt-in and stored credentials; missing credentials must fail loud in Settings, not silently drop reminders.
- A cancelled/rescheduled appointment must reliably cancel its old pending reminders — a stale reminder firing for a cancelled appointment is a real patient-trust failure, test this explicitly.
- Reply tokens must be single-use or expiring, and must not leak other appointment/patient data if guessed/brute-forced (long random token, rate-limited endpoint).
- The 24h reminder is described in `mvp.md` §8.8 as "guaranteed" and never replaced by later AI-driven smart timing — this phase's deterministic schedule is permanent, not something Phase 19's no-show prediction feature overrides.
- Recall generation must not create duplicate open recalls for the same patient/reason if the job re-runs (idempotent by `patient_id + source + due_date` or similar).
- Never log full patient contact info or message content in application logs (PHI safety) — log reminder IDs/status only.

## Testing

- pytest: reminder side-effects on create/reschedule/cancel, ARQ dispatch job sends only due reminders, SMS blocked without opt-in/credentials, recall generation idempotency
- Vitest: notification preferences form, recall board actions
- Playwright: book an appointment, verify a confirmation reminder row is created (mock the send, assert the DB state and a test outbox)

## Docs to update in this phase

- `docs/architecture/data-model.md`
- `docs/guides/routes/dashboard/settings/notifications.md`, `dashboard/recalls.md`
- `mvp.md` §15 open question #3 (SMS cost ownership) — flag as still needing a business decision if unresolved

## Exit criteria

- [x] Confirmation + 24h reminder fire reliably for every new appointment (tested)
- [x] Reschedule/cancel correctly cancels stale reminders and sends the right notice
- [x] Recalls generate from follow-up dates and surface on a dedicated board + dashboard widget
- [x] `pnpm run ci:quality` green
