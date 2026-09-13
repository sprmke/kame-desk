# Appointments list (`/dashboard/appointments`)

**Status:** Documented

## Behavior

- Chronological list with patient, doctor name (never a UUID), Manila-local time, status (shape plus label, not a pastel pill), reason.
- The fixed **Schedule** title and description sit above the List / Calendar tabs; the appointment content renders below the tabs. **New appointment** is contributed to the section header by this tab. Switching tabs changes only the content, never the title or description.
- Shared list chrome: live search, status, doctor and date-range filters, sort, per-page (25/50/100), and Table / List / Calendar views. The range picker uses one calendar: select the start, then the end, and the interval stays highlighted. Phone defaults to List. Calendar view uses the same filters and hides page numbers. Query params remain `q`, `status`, `doctorId`, `from`, `to`, `page`, `limit`, `sort`, `view`. Report bars can pre-fill `from`, `to`, and `doctorId`. Empty and error states use the same bordered card as the table.
- A dedicated `/dashboard/appointments/calendar` route still exists for FullCalendar drag-reschedule. The list Calendar view is a month board on this page.
- Public bookings that still need review appear in **Public requests** when auto-confirm is off. Confirmed or staff bookings from the public link show a Public badge.
- **Waitlist** holds patients who want an earlier slot. Its patient picker searches the server after a short debounce and loads 25 more results near the end of the menu, so it does not load the clinic roster into the page. Add or remove from the list. An empty waitlist uses `EmptyState`.
- **Cancel** and **No show** actions on each active row.
- **Phone/tablet:** swipe a row left to reveal Cancel / No show, then tap to run the action. With Reduce Motion, the buttons stay on the row. Recurring cancel still opens the scope picker as a bottom sheet. Bottom tab **Calendar**.
- Recurring appointments: cancel opens scope picker (this / this and following / all).
- **New appointment** opens booking form (single or recurring).
- **SOAP** link on each row opens the versioned chart for that visit.

## Save paths

| Action         | API                                                                                                         | DB effect                         |
| -------------- | ----------------------------------------------------------------------------------------------------------- | --------------------------------- |
| List           | `GET /api/v1/appointments` (filters: q, status, doctor, dates, booking_source, room, page, page_size, sort) | read                              |
| Confirm public | `PATCH /api/v1/appointments/{id}`                                                                           | `appointment_status = Confirmed`  |
| Waitlist       | `GET/POST /api/v1/appointments/waitlist`                                                                    | `appointment_waitlist`            |
| Cancel         | `DELETE /api/v1/appointments/{id}?scope=...`                                                                | `appointment_status = Cancelled`  |
| No show        | `POST /api/v1/appointments/{id}/mark-no-show`                                                               | status + `patients.no_show_count` |

## RBAC

`owner`, `admin`, `doctor`, `reception`.

## Edge cases

- No show only after `scheduled_end` has passed.
- Scope `all` cancels every non-terminal occurrence in the series.

## Implementation map

- Web: `AppointmentListPage.tsx`, `AppointmentRowActions.tsx`, `SeriesScopeDialog.tsx`
- API: `appointments.py`, `walkin_service.py`, `recurring_service.py`

## Host-facing knowledge

Past appointments can be marked **No show**. Recurring bookings show a scope choice when you cancel. On a phone, swipe a row left to show Cancel or No show, then tap to confirm. If Reduce Motion is on, Cancel and No show stay on the row. Switch Table, List, or Calendar from the view menu.
