# Platform (`/platform`)

**Status:** Documented

## Behavior

- Super admin only (`PLATFORM_ADMIN_EMAILS`).
- Tenants: live search, sort, per-page, Table / List (same list chrome as clinic lists). Suspend/reactivate, change plan, and support login (30 minutes, banner in the clinic app). The API still returns the full tenant list; the page paginates in the browser.
- Flags: AI assistant kill switch (DB overrides env when a row exists).
- Metrics: clinic counts by status, appointments, AI requests/tokens, SMS sent/failed, file counts, and per-clinic AI request totals. No patient content.

## Save paths

| Action        | API                                       | Effect                       |
| ------------- | ----------------------------------------- | ---------------------------- |
| List          | `GET /platform/tenants`                   | read                         |
| Patch         | `PATCH /platform/tenants/{id}`            | status/plan + platform audit |
| Support login | `POST /platform/tenants/{id}/impersonate` | owner access token           |
| Flag          | `PATCH /platform/flags/{key}`             | platform audit               |

## RBAC

Platform allow-list. Clinic roles cannot open these routes usefully (API 403).

## Implementation map

- Web: `apps/web/src/features/platform/`
- API: `apps/api/app/routers/platform.py`

## Host-facing knowledge

Platform is for DoctorDesk operators, not clinic staff. Search clinics, sort, and switch Table or List. Support login is audited. Suspended clinics cannot use the dashboard.
