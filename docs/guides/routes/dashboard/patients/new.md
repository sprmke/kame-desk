# New patient (`/dashboard/patients/new`)

**Status:** Documented

## Behavior

- Required: full name and data-processing consent. Fields use shared placeholders and inline validation.
- Optional: birthdate, contact, email, address, HMO provider, member ID.
- Possible matches (same name or contact) appear before save so staff can open the existing chart instead of creating a duplicate.

## Save paths

| Action           | API                            | DB                                        |
| ---------------- | ------------------------------ | ----------------------------------------- |
| Possible matches | `GET /api/v1/patients/matches` | `patients`                                |
| Create           | `POST /api/v1/patients`        | `patients` + empty `patient_medical_info` |

## RBAC

`owner`, `admin`, `doctor`, `reception`.

## Implementation map

- Web: `apps/web/src/features/patients/pages/PatientNewPage.tsx`
- API: `apps/api/app/routers/patients.py`

## Host-facing knowledge

Add a person only after checking they are not already in the registry. If a possible match appears, open that chart instead of creating a second one.
