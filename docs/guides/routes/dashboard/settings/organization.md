# `/dashboard/settings/organization`

**Status:** Documented

## Behavior

Org owners see their organization name, subscription plan/status, enrolled clinics (with enrollment badges), and an **Add clinic** action. Staff who are not org owners do not see this page (gated by `settings:organization` on `/auth/me`).

Adding a clinic creates it under the org with `pending_enrollment`. The owner is redirected to `/onboarding` for the new clinic. Super Admin activates enrollment via `/platform/tenants/{org_id}`.

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

- One account can own multiple organizations.
- Each organization can have multiple clinics (plan limits apply).
- New branches need platform activation before doctor invites and public booking go live.
- Patient records do not sync across clinics in the same org.
