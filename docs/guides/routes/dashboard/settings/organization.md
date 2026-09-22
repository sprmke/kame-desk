# `/dashboard/settings/organization`

**Status:** Out of MVP (v1.2). Staff route redirects to Billing plan. APIs remain for Phase 2 multi-clinic.

Org owners do not see this page in the solo-clinic MVP. Super Admin still manages tenants on `/platform`.

## Behavior

`/dashboard/settings/organization` and `/dashboard/settings/organization/clinics/new` redirect to `/dashboard/settings/plan`. Add clinic is hidden in this MVP. Org APIs stay for Phase 2.

Adding a clinic (API) creates it under the org with `pending_enrollment`. Super Admin activates enrollment via `/platform/tenants/{org_id}`.

## Save paths

| UI action  | API                                           | DB effect                                                        |
| ---------- | --------------------------------------------- | ---------------------------------------------------------------- |
| Add clinic | `POST /api/v1/organizations/{org_id}/clinics` | `clinics`, `clinic_memberships`, `organization_enrolled_clinics` |
| View org   | `GET /api/v1/organizations/{org_id}`          | read-only                                                        |

## RBAC

- Org settings: org owner only (`settings:organization` permission)
- Clinic operations: unchanged (`X-Clinic-Id` + clinic role)

## Implementation map

- Web: `apps/web/src/features/settings/organization/`, routes `dashboard.settings.organization*`
- API: `apps/api/app/routers/organizations.py`, `organization_service.py`

## Host-facing knowledge

This MVP is one clinic. Organization and add-clinic screens are hidden. Super Admin still manages tenants on Platform.
