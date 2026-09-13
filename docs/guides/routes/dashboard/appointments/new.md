# New appointment (`/dashboard/appointments/new`)

**Status:** Documented

## Behavior

- Select patient, doctor (by name), optional type (service duration), optional room, date, time (Manila wall clock), duration. Required fields use a mark and inline errors. Reason uses a shared placeholder.
- Optional **Recurring** with weekly / biweekly / monthly presets (12 occurrences).
- Client-side conflict pre-check against same-day appointments for the doctor.
- Recurring create returns expansion summary; conflicts are listed if any occurrence could not be booked.
- Once a patient is selected, a compact eligibility check widget (`PatientEligibilityCard`, Phase 33) appears below the form so front desk can verify HMO/PhilHealth coverage before booking without leaving the page.

## Save paths

| Action         | API                               | DB                                   |
| -------------- | --------------------------------- | ------------------------------------ |
| Single book    | `POST /api/v1/appointments`       | one `appointments` row               |
| Recurring book | `POST /api/v1/appointment-series` | `appointment_series` + expanded rows |

## Validation

- Slot must fall within clinic working hours (single book).
- Overlapping active appointments return 409 (single) or per-occurrence conflict (series).

## RBAC

All four staff roles.

## Implementation map

- Web: `AppointmentNewPage.tsx`, `rrulePresets.ts`, `conflictCheck.ts`, `PatientEligibilityCard.tsx`
- API: `appointment_service.create_appointment`, `recurring_service.create_appointment_series`

## Host-facing knowledge

Turn on **Recurring** for follow-up series. If some dates conflict, you will see how many could not be booked.
