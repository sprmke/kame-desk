# Public booking (`/book/:clinicSlug`)

**Status:** Documented

## Behavior

- No login required.
- Shows clinic name, address, doctors, calendar date picker, available slot pills, guest name and contact (shared placeholders). No slots uses a compact empty state in a card; slot fetch uses pill skeletons.
- Submits a booking request; auto-confirms when clinic setting is on.
- Optional **Chat** widget calls `POST /api/v1/public/clinics/{slug}/assistant/messages` (SSE, anonymous, rate-limited). Grounded on clinic hours/services only.

## Save paths

| Action      | API                                                       | DB                                                                      |
| ----------- | --------------------------------------------------------- | ----------------------------------------------------------------------- |
| Load clinic | `GET /api/v1/public/clinics/{slug}`                       | `clinics`, `doctor_profiles`, `service_fees`                            |
| Load slots  | `GET /api/v1/public/clinics/{slug}/available-slots`       | computed from working hours + `appointments`                            |
| Book        | `POST /api/v1/public/clinics/{slug}/appointment-requests` | `patients` (find/create), `appointments` (`booking_source=public_link`) |
| Assistant   | `POST /api/v1/public/clinics/{slug}/assistant/messages`   | `patient_assistant_conversations`, `patient_assistant_messages`         |

## Validation

- Slot must still be open at submit (409 if taken).
- IP rate limit on public endpoints.

## RBAC

None (public). Scoped by clinic slug only.

## Implementation map

- Web: `apps/web/src/features/booking/pages/PublicBookingPage.tsx`, `PublicAssistantChat.tsx`
- API: `apps/api/app/routers/public_booking.py`, `slot_service.py`

## Host-facing knowledge

Share the **Public link** from the staff calendar. Patients pick a doctor, date, and time without calling. If **Auto-confirm public bookings** is off, requests stay `Scheduled` until staff confirms. The page has a sun/moon button (top right) for light or dark.
