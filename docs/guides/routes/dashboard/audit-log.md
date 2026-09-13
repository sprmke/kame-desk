# Activity log (`/dashboard/audit-log`)

**Status:** Documented

## Behavior

- The fixed **Insights** title and description sit above the Reports / Activity log tabs; the audit controls render below the tabs. Switching tabs changes only the content, never the title or description.
- Paginated clinic activity log for owner, admin, and doctor roles.
- Shared list chrome: search by action, actor/action/target filters, one date-range picker (start click, then end click, writing both `from` and `to`), sort, per-page, Table / List views. Phone defaults to List.
- Append-only: no edit or delete in the app; DB trigger rejects updates.
- The empty state explains that this is an audit trail and describes how to filter. Empty and error states use the same bordered card as the table.

## Save paths

Read-only. `GET /api/v1/clinics/{id}/activity-log` (`page`, `page_size`, `q`, `sort`, actor/action/target, dates).

Contextual trails on patient, invoice, and SOAP (appointment) pages use the same endpoint with `target_type` and `target_id`.

## RBAC

Owner, admin, and doctor. Reception is blocked (403).

SOAP-related rows strip `metadata` for admin viewers. Summaries never include clinical note text.

## Implementation map

- Web: `apps/web/src/features/audit-log/`
- API: `apps/api/app/routers/activity_log.py`, `apps/api/app/services/activity_log_service.py`
- Migration: `014_activity_log_hardening.py` (indexes + append-only trigger)

## Host-facing knowledge

The activity log shows who changed what and when. Search by action, filter, sort, and switch Table or List. It cannot be edited. Doctors and owners see full detail; admins see actions but not SOAP metadata side channels.
