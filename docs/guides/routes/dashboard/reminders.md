# Reminders (`/dashboard/outreach/reminders`)

**Status:** Documented

## Behavior

- Clinic-wide reminder list with status filter (pending, sent, failed, cancelled). Shared list chrome: debounced search, sort, per-page, Table / List. Search, sort, and pagination run on the API; the browser keeps only the current page. Empty and error states use the same bordered card as the table. The "No reminders" count line is hidden while the empty card is showing.
- Each row shows its channel (`email` / `sms` / `whatsapp`) alongside type and status. No separate channel filter yet.
- Failed rows show Retry. The dashboard home also lists failed sends with Retry.
- The fixed **Outreach** title and description sit above the Reminders / Recalls tabs; the reminder content renders below the tabs. Switching tabs changes only the content, never the title or description.

## Save paths

| Action | API                                 | Effect                     |
| ------ | ----------------------------------- | -------------------------- |
| List   | `GET /api/v1/reminders/search`      | paginated read             |
| Retry  | `POST /api/v1/reminders/{id}/retry` | resend; `reminder.retried` |

## RBAC

Clinic staff.

## Implementation map

- Web: `apps/web/src/features/reminders/pages/ReminderDashboardPage.tsx`
- API: `apps/api/app/routers/reminders.py`

## Host-facing knowledge

Reminders show what the clinic sent or tried to send. Search, filter by status, sort, and switch Table or List. Retry only works on failed rows. A patient can opt out on their chart.
