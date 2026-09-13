# Phase 12: Reports & analytics

**Status:** Done
**Depends on:** Phase 11
**Unlocks:** Phase 13

**mvp.md reference:** §6.10 · Gap closed: #14 in §7

## Goal

Give a clinic trustworthy numbers behind the dashboard's revenue/appointment summaries: appointments booked vs. completed vs. no-show trends, revenue breakdowns, patient growth, top diagnoses/visit reasons, all exportable to CSV.

## Prerequisites

- Phase 11 done — this phase is read-only reporting over data every prior phase already wrote (appointments, visit status events, invoices, payments, SOAP diagnoses)

## Tasks

### 1. Backend

- [x] `GET /api/v1/reports/appointments` — grouped by day/week/month/doctor; booked vs. completed vs. no-show counts, derived from `appointments.appointment_status` + `visit_status_events` (Phase 5)
- [x] `GET /api/v1/reports/revenue` — grouped by day/week/month/service-type/doctor, derived from `invoices`/`invoice_line_items`/`payments` (Phase 9)
- [x] `GET /api/v1/reports/patient-growth` — new vs. returning patients over time, derived from `patients.created_at` + appointment history
- [x] `GET /api/v1/reports/top-diagnoses` — aggregated from `soap_notes.diagnosis_primary`/`icd10_codes` (Phase 7), respecting the RBAC rule that admins never see full clinical notes — this report must expose diagnosis _labels in aggregate_, never linked back to an individual patient record for a role that shouldn't see clinical content directly; decide and document whether admins can see this report at all, or only owner/doctor can (recommend: owner and doctor only, matching §6.11's clinical-notes row)
- [x] `GET /api/v1/reports/{report}/export.csv` — CSV export for each report type, respecting the same RBAC per report
- [x] All report queries must be clinic-scoped and should use materialized/aggregated queries (not N+1 loops) — this is the first phase where query performance at scale actually matters; add appropriate indexes (composite on `clinic_id + created_at`/`scheduled_start` etc.)

### 2. Frontend

- [x] `src/features/reports/` — chart views per report (simple bar/line charts, no heavy BI tooling needed for MVP), date-range picker, doctor filter, CSV export button
- [x] Dashboard summary widgets (§6.2 revenue summary) upgraded to pull from the same report endpoints rather than ad-hoc queries duplicated between Phase 9 and this phase — refactor Phase 9's dashboard widget to call the Phase 12 endpoint if the shapes converge

## Data model

No new tables — this phase is entirely derived/aggregated from existing data. Consider a `reporting` schema of SQL views if query complexity grows, but don't over-engineer for MVP scale (a solo clinic's data volume is small).

## API endpoints

| Method | Path                                  | Roles                                      |
| ------ | ------------------------------------- | ------------------------------------------ |
| GET    | `/api/v1/reports/appointments`        | owner, admin                               |
| GET    | `/api/v1/reports/revenue`             | owner, admin                               |
| GET    | `/api/v1/reports/patient-growth`      | owner, admin                               |
| GET    | `/api/v1/reports/top-diagnoses`       | owner, doctor only (clinical content rule) |
| GET    | `/api/v1/reports/{report}/export.csv` | same as the matching report                |

## Edge cases & safety

- Top-diagnoses aggregation must not become a backdoor to clinical content for a role that's supposed to be blocked from it (admin) — verify with an actual access-control test, matching the same rigor `mvp.md` §12 demands for SOAP RBAC.
- CSV exports containing patient-identifying data (if any report does — most should be aggregate-only) must go through the same PHI-safety review as any other export; prefer aggregate-only reports for MVP and defer per-patient exportable lists to a clinic's explicit "Data export" setting (§6.12), not this reporting module.
- Reports spanning a doctor who has since left the clinic (deactivated membership) must still show historical data correctly — don't let a deactivated membership silently exclude past records from aggregates.

## Testing

- pytest: aggregation correctness against seeded fixture data, RBAC on top-diagnoses, CSV export shape
- Vitest: chart rendering with empty/sparse data (don't crash on a brand-new clinic with zero history)
- No new Playwright spec required unless a report page has complex interaction; smoke-test load is enough

## Docs to update in this phase

- `docs/architecture/api-conventions.md` — document the reporting endpoint pattern (date-range params, CSV export convention) once, reused by future reports
- `docs/guides/routes/dashboard/reports.md`

## Exit criteria

- [x] All four report types return correct aggregates against seeded test data
- [x] CSV export works for each
- [x] Top-diagnoses RBAC verified by test, not read-through
- [x] `pnpm run ci:quality` green
