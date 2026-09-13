# Phase 13: Audit log surfaced in UI

**Status:** Done
**Depends on:** Phase 12
**Unlocks:** Phase 14

**mvp.md reference:** §6.11 (UI half — backend logging exists from Phase 1 onward) · Gap closed: #13 in §7

## Goal

Every phase since Phase 1 has been writing to `activity_log`. This phase makes that log visible, searchable, and trustworthy for doctors/owners/admins reviewing "what happened and who did it" — the first phase that is pure hardening rather than new backend capability, and a natural checkpoint to audit that every prior phase actually did log correctly before AI-driven writes (Phase 14+) add a second class of actor to that same log.

## Prerequisites

- Phase 12 done. This phase also functions as an **audit pass** over Phases 1–12: confirm every mutating endpoint built so far actually writes to `activity_log`. Treat any gap found as a bug to fix in this phase, not a note for later.

## Tasks

### 1. Backend

- [x] Audit sweep: grep every `POST`/`PATCH`/`DELETE` endpoint built in Phases 1–12 against `activity_log` write sites; list any gap in this phase's PR description and fix it here
- [x] `GET /api/v1/clinics/{id}/activity-log` — paginated, filterable by actor, action type, target type, date range
- [x] Ensure `activity_log.actor_type` already distinguishes `user`/`system`/`ai_assistant` (set up in Phase 1) — this phase doesn't add AI actors yet (that's Phase 16) but the schema must already support it without a migration later
- [x] Confirm the log is genuinely append-only — no `UPDATE`/`DELETE` endpoint exists for `activity_log` rows anywhere in the codebase; add a DB-level safeguard if feasible (e.g. revoke UPDATE/DELETE grants on the table for the app's DB role, or a trigger that rejects them) as a defense-in-depth measure beyond "no endpoint exists"

### 2. Frontend

- [x] `src/features/audit-log/` — filterable, paginated log view (owner/admin only, per §6.11 "Doctors and admins can view the activity log for their own clinic")
- [x] Contextual audit trail: a small "Activity" tab/section on the patient detail page, appointment detail page, and invoice detail page showing just the entries scoped to that record (reuses the same endpoint with a `target_type`+`target_id` filter)

## Data model

No new tables — `activity_log` already exists from Phase 1. This phase may add indexes (`clinic_id + created_at`, `target_type + target_id`) to keep the filtered views fast.

## API endpoints

| Method | Path                                | Roles                                             |
| ------ | ----------------------------------- | ------------------------------------------------- |
| GET    | `/api/v1/clinics/{id}/activity-log` | owner, admin, doctor (own-clinic view, per §6.11) |

## Edge cases & safety

- The log itself must never be editable or deletable through the app, by any role, including owner — this is explicit in `mvp.md` §6.11.
- Filtering by target must respect the same RBAC as the underlying record — a reception account without SOAP access must not be able to read SOAP-content details through the audit log's `summary`/`metadata` fields as a side channel; audit log summaries for clinical actions should describe the _action_ ("SOAP note saved, version 3"), never embed the clinical content itself.
- Pagination must perform well once a clinic has months of history — verify with a seeded large dataset, not just a handful of rows.

## Testing

- pytest: the audit-sweep gap-fix work is itself tested (assert a write to every mutating endpoint from Phases 1–12 produces exactly one `activity_log` row, no duplicates from a single logical action)
- pytest: RBAC filter (reception blocked from clinical-content audit details)
- Vitest: filter UI, contextual tab rendering
- Playwright: perform a mutating action (e.g. reschedule an appointment), verify it appears in the audit log UI within the same session

## Docs to update in this phase

- `docs/architecture/security-compliance.md` — confirm the audit-logging invariant section matches what's actually enforced (DB-level or app-level) after this phase's defense-in-depth work
- `docs/guides/routes/dashboard/audit-log.md`
- `mvp.md` §12 checklist — this phase directly satisfies "Audit log (`activity_log`) covers every mutating action across manual UI and AI assistant paths" (the manual-UI half; the AI half is verified again in Phase 16)

## Exit criteria

- [x] Every mutating endpoint from Phases 1–12 confirmed (by test, not inspection) to write `activity_log`
- [x] Audit log UI is filterable, paginated, and performant against a realistic data volume
- [x] Clinical content never leaks into an audit summary visible to a role that shouldn't see it
- [x] `pnpm run ci:quality` green

## Audit sweep gaps fixed in this phase

- `PATCH /clinics/{id}/notification-preferences` — added `clinic.notification_preferences_updated` log
- `POST /doctors/{id}/signature-upload` — added `doctor.signature_updated` log
