# Pricing (`/pricing`)

**Status:** Documented

## Behavior

- Public plan cards from `GET /api/v1/plans`.
- Start trial links to `/register?plan=`.

## RBAC

Public.

## Implementation map

- Web: `apps/web/src/features/marketing/pages/PricingPage.tsx`
- API: `apps/api/app/routers/plans.py`

## Host-facing knowledge

Starter, Pro, and Clinic are 14-day trials. AI and SMS are metered on Pro and Clinic. Plan changes after signup go through platform support.
