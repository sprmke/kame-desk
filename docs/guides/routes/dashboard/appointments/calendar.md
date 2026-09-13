# Appointments calendar (`/dashboard/appointments/calendar`)

**Status:** Documented

## Behavior

- Day, week, and month views (FullCalendar). Loading uses a calendar skeleton.
- The fixed **Schedule** title and description sit above the List / Calendar tabs; the calendar renders below the tabs. **New appointment** is contributed to the section header by this tab. Switching tabs changes only the content, never the title or description.
- The appointments list (`/dashboard/appointments?view=calendar`) also has a Calendar view. Use this page when you need drag-to-reschedule, doctor/room resource grids, or auto-confirm controls.
- Filter by doctor name or room. **By doctor** shows a same-day time grid per doctor, side by side.
- Toggle color by doctor. Doctor colors come from a four-step categorical token set (no red). Appointment status colors use status CSS variables, not hardcoded hex.
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

Use **Calendar** for the day view. Drag a block to move it. If two desks move the same slot, the second change fails safely.
