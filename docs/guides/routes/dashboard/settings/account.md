# Account (`/dashboard/settings/account`)

**Status:** Documented

## Behavior

Lists active refresh sessions and lets the user sign out everywhere. Owners and admins can download patient and appointment CSV. Owners can file a clinic deletion request (timestamp only; PHI is not wiped in this step). Layout is divider rows (`SettingsSection` / `SettingsRow`), not stacked cards.

## Save paths

| Action              | API                                            | Effect                                                           |
| ------------------- | ---------------------------------------------- | ---------------------------------------------------------------- |
| List sessions       | `GET /api/v1/auth/sessions`                    | Active, unexpired refresh rows                                   |
| Sign out everywhere | `POST /api/v1/auth/logout-everywhere`          | Revoke all refresh tokens, `auth.logout_everywhere`              |
| Patients CSV        | `GET /api/v1/clinics/{id}/export/patients`     | CSV download, `clinic.data_exported`                             |
| Appointments CSV    | `GET /api/v1/clinics/{id}/export/appointments` | CSV download, `clinic.data_exported`                             |
| Request deletion    | `POST /api/v1/clinics/{id}/deletion-request`   | Set `clinics.deletion_requested_at`, `clinic.deletion_requested` |

## RBAC

Any signed-in member can list sessions and sign out everywhere. Export is owner/admin. Deletion request is owner only.

## Implementation map

- Web: `apps/web/src/features/settings/account/pages/AccountSettingsPage.tsx`
- API: `apps/api/app/routers/auth.py`, `apps/api/app/services/clinic_export_service.py`

## Host-facing knowledge

Use Account to see signed-in sessions and to sign out every device. Owners and admins can download patient and appointment lists as CSV. Requesting clinic deletion records the request; patient records are not deleted on the spot.
