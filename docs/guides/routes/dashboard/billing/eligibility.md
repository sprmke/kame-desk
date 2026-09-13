# Billing — eligibility checks

**Status:** Documented
**Route:** `/dashboard/billing/eligibility`

## Behavior

Eligibility is one tab of the Billing hub (`Invoices · Claims · Eligibility · LOA`). Structured HMO/PhilHealth coverage checks, recorded before a visit so the front desk knows what a payer will cover.

The page is a **list only**; **New check** in the section header opens a `ResponsiveModal` with patient search, payer name (autocompletes from the payer directory), payer type, and member ID. Standard `ManagedList` chrome: live search, status and payer-type filters, sort, per-page, Table / List (`q`, `status`, `payerType`, `page`, `limit`, `sort`, `view`).

- Statuses: `pending` → `verified` / `denied` / `expired`, changed inline from the row.
- History is **additive** — requesting a new check for the same patient and payer does not overwrite the prior one, since coverage changes over time.
- Search matches patient name, payer name, or member ID. Sort supports newest, oldest, status, payer, and patient.
- The same data appears compact on the patient detail Billing tab and on the new-appointment booking form (`PatientEligibilityCard`) once a patient is selected.
- Without `billing:write` the list is read-only: no New check button and the status select is disabled.

## Save paths

| Action       | API                                                                                                       | DB                                                            |
| ------------ | --------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------- |
| List checks  | `GET /api/v1/eligibility-checks` (`q`, `status`, `payer_type`, `patient_id`, `page`, `page_size`, `sort`) | `eligibility_checks`                                          |
| Create check | `POST /api/v1/eligibility-checks`                                                                         | new row, `eligibility_check.created`                          |
| Update check | `PATCH /api/v1/eligibility-checks/{id}`                                                                   | status / verified_amount / notes, `eligibility_check.updated` |

Setting status to a failed or ineligible value also triggers `notify_eligibility_updated`.

## RBAC

Create/update: owner, admin, reception (`billing:write`). Read: all clinic staff (`billing:view`), enforced by `assert_billing_read`.

## AI assistant parity

Tier 0 `check_eligibility_status` (`app/ai/assistant/tools.py`) reads the latest `EligibilityCheck` for a patient — read-only, no live insurer call. The assistant cannot create or update a check.

## Edge cases

- Requesting a check calls the configured `claims_partner`; the default `ManualClaimsPartner` is a no-op, so status stays `pending` until staff update it.
- `verified_amount` is only set when a check is marked verified; rows without it omit the amount from the subtitle.
- Listing without `page_size` returns every row (used by the patient-scoped card); the page always passes pagination.

## Implementation map

- Web: `apps/web/src/features/billing/pages/EligibilityChecksPage.tsx`, `components/EligibilityCreateModal.tsx`, `components/PatientEligibilityCard.tsx`
- Route: `apps/web/src/routes/dashboard.billing.eligibility.tsx`
- API: `apps/api/app/routers/eligibility_checks.py`, service `apps/api/app/services/eligibility_service.py`
- Migration: `030_ph_payer_workflow.py`

## Host-facing knowledge

Open **Billing → Eligibility** to record what an HMO or PhilHealth confirmed for a patient before a visit. Tap **New check** at the top right, pick the patient, and enter the payer and member ID. Once the payer replies, set the row to verified, denied, or expired. Checks are kept as history, so a new check never erases an older one — useful when a patient's coverage changes. Front desk can also record a check from the patient's chart or while booking an appointment.
