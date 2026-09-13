# Billing — HMO claims

**Status:** Documented
**Route:** `/dashboard/billing/claims`

## Behavior

Claims is one tab of the Billing hub (`Invoices · Claims · Eligibility · LOA`). The page is a **list only**: the create form lives in a modal opened from the section header, matching every other hub list page. The hub title and description are fixed and come from `billingHub`; this tab contributes a **New claim** button through `SectionHeaderActions`.

Clinic-wide list of insurance claims with status `draft` / `submitted` / `approved` / `denied` / `paid`, each tagged with a `payer_type` (HMO / PhilHealth / self-pay / other). Shared list chrome via `ManagedList`: live search, status and payer-type filters, sort, per-page, Table / List views (`q`, `status`, `payerType`, `page`, `limit`, `sort`, `view`).

- **Create:** **New claim** opens a `ResponsiveModal` (bottom sheet below `lg`, dialog at `lg+`) with patient search, HMO / payer name, payer type, member ID, and amount. The payer name field autocompletes from the clinic payer directory. Save is disabled until patient, payer name, and amount are filled. Closing the modal by any route (Cancel, X, Escape, overlay) resets the form.
- **Table columns:** Patient, Payer, Amount, LOA, Status. LOA and Status are separate columns so row heights stay uniform.
- **Status changes** stay in-app — no live insurer submission (kame-desk does not pursue its own HITP/EDI accreditation for MVP; submission goes through a pluggable `claims_partner` adapter, `ManualClaimsPartner` by default).
- **Request LOA** on an HMO claim with no linked LOA creates the LOA request and links it back to the claim. Rows already linked show `Linked`; non-HMO rows show an em-dash.
- Users without `billing:write` see the list read-only: no New claim button, no Request LOA, and the status select is disabled.

Eligibility checks, LOA requests, and the payer directory each moved to their own route — see [eligibility.md](./eligibility.md), [loa.md](./loa.md), and [../settings/payers.md](../settings/payers.md).

## Save paths

| Action                 | API                                                                             | DB                                      |
| ---------------------- | ------------------------------------------------------------------------------- | --------------------------------------- |
| List claims            | `GET /api/v1/claims` (`q`, `status`, `payer_type`, `page`, `page_size`, `sort`) | `insurance_claims`                      |
| Create claim           | `POST /api/v1/claims`                                                           | new row, `insurance_claim.created`      |
| Update claim           | `PATCH /api/v1/claims/{id}`                                                     | status / reference / payer_type / notes |
| Request LOA from claim | `POST /api/v1/loa-requests` then `PATCH /api/v1/claims/{id}`                    | `loa_requests`, claim `loa_request_id`  |

## RBAC

Create/update: owner, admin, reception (`billing:write`). Read: all clinic staff (`billing:view`).

## AI assistant parity

No assistant tool writes claims. Tier 0 `check_eligibility_status` reads coverage — see [eligibility.md](./eligibility.md).

## Edge cases

- Amount is free text validated server-side; a non-numeric value returns a 422 surfaced as an inline modal error.
- Requesting an LOA twice is prevented by hiding the action once `loa_request_id` is set.
- Claim detail (`/dashboard/billing/claims/:claimId`) renders a read-only summary. It currently resolves the claim by scanning the first page of the claims list rather than a dedicated `GET /claims/{id}`, so a claim beyond that page will not resolve.

## Implementation map

- Web: `apps/web/src/features/billing/pages/ClaimsPage.tsx`, `components/ClaimCreateModal.tsx`, `components/PayerFormFields.tsx`, `hooks/usePatientField.ts`
- Route: `apps/web/src/routes/dashboard.billing.claims.tsx`
- API: `apps/api/app/routers/claims.py`, service `apps/api/app/services/claim_service.py`
- Migration: `030_ph_payer_workflow.py`

## Host-facing knowledge

Open **Billing → Claims** to track HMO and PhilHealth claims. The page shows your claims right away; to add one, use the **New claim** button at the top right and fill in the short form that appears. Search, filter, sort, and switch Table or List the same way as other clinic lists. Move a claim from draft to submitted, approved, denied, or paid as the insurer replies. On an HMO claim you can tap **Request LOA** to start the authorization paperwork without leaving the page.
