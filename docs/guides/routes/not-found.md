# Unmatched URL (404)

**Status:** Documented

## Behavior

Any path that is not a DoctorDesk route shows **Page not found**. **Back to Today** goes to `/`, which then sends signed-in staff to `/dashboard` and everyone else to `/login`.

Unknown paths under `/dashboard` stay inside the dashboard shell.

## Save paths

None. Display only.

## RBAC

Public. No auth check on the 404 screen itself. Links into `/dashboard` still require sign-in.

## Implementation map

- Web: `apps/web/src/components/layout/NotFoundPage.tsx`
- Root: `apps/web/src/routes/__root.tsx` (`notFoundComponent`)
- Router default: `apps/web/src/router.tsx` (`defaultNotFoundComponent`)
- Dashboard: `apps/web/src/routes/dashboard.tsx` (`notFoundComponent`)

## Host-facing knowledge

If a bookmark or link is not a DoctorDesk page, you see Page not found. Tap Back to Today.

## activity-log

N/A — no mutation.
