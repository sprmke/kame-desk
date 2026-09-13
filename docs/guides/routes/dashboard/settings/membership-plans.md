# Membership plans (`/dashboard/settings/membership-plans`)

**Status:** Documented

## Behavior

Owners and admins manage the clinic's recurring care plans — a name, a price, a billing interval (monthly/quarterly/annual), and an optional list of included-service allowances (a category plus a count per billing period, e.g. "consultation x2").

The page is a **list only**. **New plan** in the page header opens a `ResponsiveModal` with name, price, billing interval, and a dynamic list of included-service rows (add/remove). The catalog and the empty state both sit in a card. Editing an existing plan reuses the same modal and also exposes an **Active** toggle — deactivating a plan hides it from the patient-enrollment picker (`GET /clinics/{id}/membership-plans` still returns it for admins, but `PatientMembershipCard` on the patient billing tab filters to `is_active` plans only). Save is disabled until name and price are filled.

Enrollment and cancellation happen on the patient's own Billing tab (`PatientMembershipCard`, `apps/web/src/features/billing/components/PatientMembershipCard.tsx`), not here — this page only defines the catalog of plans.

## Save paths

| Action                          | API                                                     |
| ------------------------------- | ------------------------------------------------------- |
| List                            | `GET /clinics/{id}/membership-plans`                    |
| Create                          | `POST /clinics/{id}/membership-plans`                   |
| Update                          | `PATCH /clinics/{id}/membership-plans/{plan_id}`        |
| Get patient's active membership | `GET /patients/{id}/membership`                         |
| Enroll patient                  | `POST /patients/{id}/membership`                        |
| Cancel patient's membership     | `POST /patients/{id}/membership/{membership_id}/cancel` |

Plan create/update requires owner or admin. Patient enroll/cancel requires clinic staff plus billing-write access (`assert_billing_write`).

## Billing integration

When an invoice line item's `category` matches an active membership's plan allowance (and the patient hasn't used up the period's count), `maybe_apply_membership_waiver` (`apps/api/app/services/membership_service.py`) automatically inserts a matching negative discount line ("Membership benefit (\<plan name\>)") and increments `usage_this_period`. This never blocks invoice creation — a waiver failure is caught and swallowed. Usage resets lazily at the next `current_period_end` rollover, computed when the membership is read.

## Implementation map

- Web: `apps/web/src/features/settings/membership/pages/MembershipPlansSettingsPage.tsx`, `.../membership/components/MembershipPlanFormModal.tsx`, `apps/web/src/features/billing/components/PatientMembershipCard.tsx`
- API: `apps/api/app/routers/membership_plans.py`, `apps/api/app/services/membership_service.py`
- Models: `MembershipPlan`, `PatientMembership` (`apps/api/app/models/membership.py`)

## Host-facing knowledge

Recurring plan charges are recorded manually (a staff member creates an invoice/payment each period) — there is no live recurring-billing gateway. The waiver only ever discounts a line item that already exists on an invoice; it never creates a charge on its own.
