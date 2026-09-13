# Billing plan (`/dashboard/settings/plan`)

**Status:** Documented

## Behavior

- Shows this clinic's `plan_key` and `status`.
- Link to public `/pricing`. Clinic staff cannot self-upgrade in-app.
- The page header describes this as the clinic's current plan and subscription status.

## RBAC

Any clinic member can view. Plan changes are platform-admin only.

## Implementation map

- Web: `apps/web/src/features/settings/pages/BillingPlanPage.tsx`

## Host-facing knowledge

Your plan and trial status live here. Ask platform support to change the plan.
