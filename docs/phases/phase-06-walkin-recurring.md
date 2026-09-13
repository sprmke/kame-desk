# Phase 6: Walk-in, reschedule, no-show, recurring series

**Status:** Done
**Depends on:** Phase 5
**Unlocks:** Phase 7

**mvp.md reference:** §6.4 (full appointment feature set), first use of ARQ background jobs

## Goal

Close out the appointment feature set: walk-ins that skip straight to `Arrived`, a proper reschedule flow (distinct history, not just an overwritten row), no-show marking (and its downstream effects), and recurring appointment series (e.g. weekly PT, monthly follow-up) expanded via `rrule` + an ARQ background job.

## Prerequisites

- Phase 5 done: visit status lifecycle + WebSocket broadcasting exist

## Tasks

### 1. Database

- [x] `appointment_series` table (per tech-stack.md's core table list) — clinic_id, doctor_id, patient_id, rrule_string, start_date, end_date (nullable = indefinite), created_by_user_id
- [x] `appointments.series_id` (nullable FK to `appointment_series`) + `appointments.series_occurrence_index`
- [x] No-show tracking: reuse `appointment_status = 'No Show'` (Phase 3); add `no_show_count` on `patients`

### 2. Backend

- [x] `POST /api/v1/appointments/walk-in` — creates a patient (if new) + appointment in one call, `appointment_status = 'Confirmed'`, `current_visit_status = 'Arrived'` immediately (skips the normal scheduled→confirmed→arrived path)
- [x] `POST /api/v1/appointments/{id}/mark-no-show` — dedicated endpoint (validates the appointment's scheduled time has passed, logs to `activity_log`, triggers Phase 11's recall/reminder logic hook once that phase exists — leave a clear extension point, don't build it yet)
- [x] `POST /api/v1/appointment-series` — creates the series row + triggers an ARQ job (`expand_recurring_series`) that generates the first N occurrences (e.g. next 90 days) as individual `appointments` rows, each independently checked against the exclusion constraint (a recurring slot that conflicts on one occurrence must not silently skip or double-book — surface the conflict to the creator for that specific date)
- [x] ARQ job: `expand_recurring_series` — idempotent (safe to re-run), extends the window periodically (e.g. a scheduled job that tops up occurrences as time passes) rather than generating years of rows up front
- [x] `PATCH /api/v1/appointments/{id}?scope=this|following|all` — edit-this-occurrence vs. edit-this-and-following vs. edit-entire-series semantics (standard recurring-event UX, same decision every calendar product makes)
- [x] `DELETE` equivalent (cancel) with the same `scope` semantics

### 3. Frontend

- [x] Walk-in quick-action button (per mvp.md §6.2 dashboard quick actions) — minimal form (patient search-or-create + doctor + reason), immediately visible in the waiting room
- [x] Recurring appointment creation UI — rrule builder (simple presets: weekly/biweekly/monthly + custom, avoid exposing raw RRULE syntax to users)
- [x] Edit/cancel dialogs with the this/following/all scope choice, matching Google Calendar's UX pattern for familiarity

## Data model

New: `appointment_series`. Extended: `appointments` (series linkage).

## API endpoints

| Method       | Path                                     | Roles                           |
| ------------ | ---------------------------------------- | ------------------------------- |
| POST         | `/api/v1/appointments/walk-in`           | owner, admin, doctor, reception |
| POST         | `/api/v1/appointments/{id}/mark-no-show` | owner, admin, doctor, reception |
| POST         | `/api/v1/appointment-series`             | owner, admin, doctor, reception |
| PATCH/DELETE | `/api/v1/appointments/{id}?scope=...`    | owner, admin, doctor, reception |

## Edge cases & safety

- A recurring series occurrence that conflicts with an existing booking must not silently disappear — the creator must see exactly which date(s) failed and why, and be able to manually resolve each one.
- Editing "this and following" mid-series must correctly split the series (the old series keeps its past+edited-boundary occurrences; a new series or a flagged branch covers the rest) — document the exact data model choice in `docs/architecture/data-model.md` once decided, this is a common source of bugs.
- The ARQ expansion job must be safe to run twice (e.g. a retry after a worker crash) without creating duplicate occurrence rows — use a natural unique constraint (`series_id + occurrence_index` or `series_id + scheduled_start`).
- Walk-in patient creation reuses the same fuzzy-search-first flow as Phase 3's patient creation to avoid duplicate patient records for a hurried front-desk entry.

## Testing

- [x] pytest: recurring expansion idempotency, conflict-on-one-occurrence handling, this/following/all edit semantics, walk-in happy path
- [x] Vitest: rrule preset builder output correctness
- [ ] Playwright: create a weekly recurring series, verify occurrences appear correctly on the calendar across several weeks (deferred to Phase 19 hardening)

## Docs to update in this phase

- [x] `.cursor/rules/appointment-workflow.mdc` — recurring series editing semantics
- [x] `docs/architecture/data-model.md` — `appointment_series` + the this/following/all data model decision
- [x] `docs/guides/routes/dashboard/appointments/` — walk-in + recurring UX

## Exit criteria

- [x] Walk-ins work end-to-end without a pre-existing appointment
- [x] Recurring series expand correctly and handle conflicts explicitly, never silently
- [x] No-show marking is auditable and has a clear extension point for Phase 11's recall logic
- [x] `pnpm run ci:quality` green
