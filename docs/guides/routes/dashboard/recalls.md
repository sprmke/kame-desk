# Recalls (`/dashboard/outreach/recalls`)

**Status:** Documented

## Behavior

- Lists `patient_recalls` (from SOAP follow-up dates and chronic-condition rules) with status filter (pending default).
- Shared list chrome: live search, sort, per-page, Table / List. Query params: `q`, `status`, `page`, `limit`, `sort`, `view`. Empty and error states use the same bordered card as the table.
- Staff can mark contacted or dismissed, or open new appointment booking with the patient pre-selected.
- The fixed **Outreach** title and description sit above the Reminders / Recalls tabs; the recall content renders below the tabs. Switching tabs changes only the content, never the title or description.
- Dashboard home shows a pending follow-ups card (top 5) for owner, admin, and reception.

## Save paths

| Action        | API                                                            | DB                    |
| ------------- | -------------------------------------------------------------- | --------------------- |
| List          | `GET /clinics/{id}/recalls` (`q`, `page`, `page_size`, `sort`) | `patient_recalls`     |
| Update status | `PATCH /recalls/{id}`                                          | status + activity log |

Recall rows are created by ARQ job `generate_recalls_job` (daily) from SOAP `follow_up_date` and chronic rules.

## RBAC

Owner, admin, and reception.

## Public reply

Patients use `/reminders/{token}` (no login) to confirm, cancel, or request reschedule via `POST /api/v1/public/reminders/{token}/respond`.

## Implementation map

- Web: `apps/web/src/features/recalls/pages/RecallsPage.tsx`, dashboard card in `apps/web/src/features/dashboard/`
- Public: `apps/web/src/features/reminders/pages/PublicReminderPage.tsx`
- API: `apps/api/app/routers/recalls.py`, `public_reminders.py`
- Jobs: `apps/api/app/workers/main.py`

## Host-facing knowledge

The recalls board shows patients due for follow-up from signed SOAP notes or chronic-care rules. Search, filter status, sort, and switch Table or List. Book from a row to schedule a return visit. Patients can confirm or cancel from the link in reminder emails.
