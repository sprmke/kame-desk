# Public booking (`/book/:clinicSlug`)

**Status:** Documented

## Behavior

- No login required.
- Shows clinic name and address. Type picker first when the clinic has services; then date; then slot pills sized to that type's duration (clinic default if the type has none). Name and phone are always required. Extra fields (email, birthdate, sex, address, reason, new/existing, notes) appear only when the clinic turns them on under Hours.
- One doctor is selected automatically. A doctor picker appears only when more than one doctor exists.
- Dates are limited to today through the clinic's advance-booking window. Slots skip lunch breaks and leave a buffer after existing appointments.
- Confirm shows clinic name, the chosen time, the type, and the cancel-notice line when set. It does not repeat the patient's contact or medical details.
- Auto-confirm still comes from the clinic setting. If it is off, the confirm line says the request was received.
- **Patient chat assistant is hidden** in this MVP. The public API remains.

## Save paths

| Action      | API                                                       | DB                                                                                                                            |
| ----------- | --------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| Load clinic | `GET /api/v1/public/clinics/{slug}`                       | `clinics`, `doctor_profiles`, `service_fees` (id, amount, `duration_minutes`)                                                 |
| Load slots  | `GET /api/v1/public/clinics/{slug}/available-slots`       | working hours + `breaks[]` + `slot_buffer_minutes` + `appointments`                                                           |
| Book        | `POST /api/v1/public/clinics/{slug}/appointment-requests` | `patients` (find/create; fill blank profile fields), `appointments` (`booking_source=public_link`, optional `service_fee_id`) |
| Assistant   | `POST /api/v1/public/clinics/{slug}/assistant/messages`   | `patient_assistant_conversations`, `patient_assistant_messages`                                                               |

## Validation

- Slot must still be open at submit (409 if taken or no longer in the computed window).
- Enabled intake fields are required except notes.
- Dates past `advance_booking_days` return no slots.
- IP rate limit on public endpoints.

## RBAC

None (public). Scoped by clinic slug only.

activity-log: booking reuses `appointment.created` from `appointment_service`. Intake GETs are N/A (read).

## Implementation map

- Web: `apps/web/src/features/booking/pages/PublicBookingPage.tsx`, `PublicAssistantChat.tsx`
- API: `apps/api/app/routers/public_booking.py`, `slot_service.py`

## Host-facing knowledge

Share the **Public link** from the staff calendar. Patients pick a visit type (if you added services), a date, and a time without calling. Extra questions on that page are the ones you turned on under Hours. If **Auto-confirm** is off, the request stays Scheduled until someone on staff confirms. The thank-you screen shows the time they booked, not their medical record.
