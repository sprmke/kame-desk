# Appointments calendar (`/dashboard/appointments/calendar`)

**Status:** Documented

## Behavior

- Day, week, and month views (FullCalendar). Loading uses a calendar skeleton.
- One doctor calendar. Doctor/room filters, **By doctor** columns, and color-by-doctor are Phase 2.
- Drag an event to reschedule; optimistic update rolls back on 409.
- **Auto-confirm public bookings** toggle and public link preview.

## Save paths

| Action              | API                                          | DB                                                                          |
| ------------------- | -------------------------------------------- | --------------------------------------------------------------------------- |
| Load events         | `GET /api/v1/appointments`                   | `appointments`                                                              |
| Drag reschedule     | `PATCH /api/v1/appointments/{id}/reschedule` | `appointments` + `activity_log` (`appointment.rescheduled` with prior slot) |
| Toggle auto-confirm | `PATCH /api/v1/clinics/{id}`                 | `clinics.public_booking_auto_confirm`                                       |

## RBAC

All four staff roles.

## Implementation map

- Web: `apps/web/src/features/appointments/calendar/pages/AppointmentCalendarPage.tsx`
- API: `appointment_service.reschedule_appointment`, `slot_service.get_available_slots`

## Host-facing knowledge

Use **Calendar** for the week view. Drag a block to move it. Share **Public link** so patients pick a type, date, and time without calling. Auto-confirm and extra public questions also live under Hours.
