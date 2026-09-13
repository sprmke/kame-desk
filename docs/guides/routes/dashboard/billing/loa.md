# Billing — LOA requests

**Status:** Documented
**Route:** `/dashboard/billing/loa`

## Behavior

LOA is one tab of the Billing hub (`Invoices · Claims · Eligibility · LOA`). Tracks the Letter of Authorization lifecycle with an HMO, which can start before a claim exists.

The page is a **list only**; **New request** in the section header opens a `ResponsiveModal` with patient search and HMO / payer name (autocompletes from the payer directory). Standard `ManagedList` chrome: live search, status filter, sort, per-page, Table / List (`q`, `status`, `page`, `limit`, `sort`, `view`).

- Statuses: `requested` → `submitted` → `approved` / `denied`, changed inline from the row. `submitted_at` and `decided_at` are set automatically on the matching transition, server-side.
- **Claim column:** a request with no claim shows **Link claim**, which lists that patient's unlinked claims. The API rejects a claim belonging to a different patient. Linked rows show `Linked`.
- A request can also be created from the Claims tab via **Request LOA**, which links the two immediately.
- Search matches patient name, HMO name, or reference number. Sort supports newest, oldest, status, payer, and patient.
- Without `billing:write` the list is read-only: no New request button, no Link claim, and the status select is disabled.

## Save paths

| Action        | API                                                                                   | DB                                                                              |
| ------------- | ------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| List requests | `GET /api/v1/loa-requests` (`q`, `status`, `patient_id`, `page`, `page_size`, `sort`) | `loa_requests`                                                                  |
| Create        | `POST /api/v1/loa-requests`                                                           | new row, `loa_request.created`                                                  |
| Update / link | `PATCH /api/v1/loa-requests/{id}`                                                     | status, `submitted_at` / `decided_at`, `claim_id`, `loa_request.status_changed` |

Status changes also trigger `notify_loa_status`.

## RBAC

Create/update: owner, admin, reception (`billing:write`). Read: all clinic staff (`billing:view`), enforced by `assert_billing_read`.

## AI assistant parity

No assistant tool creates or updates LOA requests. Coverage questions are answered by the Tier 0 `check_eligibility_status` tool instead.

## Edge cases

- Linking a claim from another patient returns 400 (`Claim does not match patient`).
- Moving to `submitted` calls the configured `claims_partner`; the default `ManualClaimsPartner` is a no-op.
- A denied LOA does not block billing — the visit can still be billed self-pay.

## Implementation map

- Web: `apps/web/src/features/billing/pages/LoaRequestsPage.tsx`, `components/LoaCreateModal.tsx`
- Route: `apps/web/src/routes/dashboard.billing.loa.tsx`
- API: `apps/api/app/routers/loa_requests.py`, service `apps/api/app/services/loa_service.py`
- Migration: `030_ph_payer_workflow.py`

## Host-facing knowledge

Open **Billing → LOA** to track a Letter of Authorization from request through approval or denial. Tap **New request** at the top right, choose the patient, and enter the HMO. You can request an LOA before any claim exists and attach the claim later with **Link claim**. A denied LOA does not block billing; the visit can still be billed as self-pay.
