# Phase 34: BIR compliance depth

**Status:** Done
**Depends on:** Phase 26
**Unlocks:** —

**Plan reference:** `docs/workflow/planned/clinic-software-market-research-feature-gaps.md` §4.1 #3

## Production defaults (resolves plan §5 open decision 3)

- BIR PTU/CAS/EIS accreditation is each clinic's own responsibility (kame-desk is the "clinic's own responsibility, we provide the configurable/compliant fields" model from plan §5.3) — kame-desk does not pursue its own CAS accreditation for MVP. What kame-desk owns: making the generated receipt/invoice contain every field a clinic needs to satisfy its own PTU/CAS filing, and a compliance-settings surface that makes the clinic's chosen configuration explicit rather than silent.
- This does not block invoice/receipt issuance — it adds fields and a settings surface, not a new approval gate.

## Goal

A clinic's receipts carry the structured fields (TIN, permit/accreditation number, VAT/non-VAT breakdown, "This document is not valid for claim of input tax" style disclosures where applicable) a bookkeeper needs for BIR filing, and the clinic can declare its own compliance mode instead of relying on a bare "numbering format" setting.

## Tasks

### Backend

- [x] Extend `Clinic`: `bir_compliance_config` (JSONB) — TIN, registered business name/address, PTU or CAS or "not yet accredited" mode, VAT registration status (VAT/non-VAT), authority-to-print or CAS accreditation number + validity dates
- [x] Extend `Invoice`/receipt PDF generation: render TIN, registered name, permit/accreditation number, VAT breakdown (vatable sales / VAT amount) when clinic is VAT-registered, "non-VAT" disclosure line when not
- [x] Validation: never hard-block invoice issuance when `bir_compliance_config` is unset — surfaced instead as a non-blocking banner on the Billing invoices page (some clinics legitimately operate below BIR registration thresholds)
- [x] `activity_log`: `clinic.bir_compliance_updated`

### Frontend

- [x] Settings → Clinic compliance section: TIN, business name/address, VAT status, PTU/CAS number + validity, compliance mode selector
- [x] `bir_compliance` embedded on `ClinicRead` so the settings form and the invoice-list banner read from the same clinic query (same visibility model as `receipt_numbering`)
- [x] Live "Preview receipt" button renders a sample receipt PDF from the current (even unsaved) form values via `POST /clinics/{id}/bir-compliance/preview`
- [x] Non-blocking banner on Billing → Invoices when compliance fields are incomplete or expired

## Edge cases

- Clinic below BIR VAT threshold (non-VAT) → omit VAT breakdown, show non-VAT disclosure line instead
- PTU/CAS validity date expired → banner warning, does not block issuance (legal risk stays with the clinic, we surface it)
- Multi-branch clinic with one TIN, multiple registered addresses → out of scope for MVP (multi-branch stays deferred per `mvp.md` §14)

## Docs to update

- [x] `docs/mvp.md` §6.7 — replace "configurable to match... BIR Official Receipt numbering" with the fuller compliance-fields description
- [x] `docs/architecture/data-model.md` — `bir_compliance_config` shape
- [x] `docs/guides/routes/dashboard/settings/clinic.md`
- [x] `docs/guides/routes/dashboard/billing/invoices.md`

## Exit criteria

- [x] Receipt PDF contains TIN, registered name, VAT/non-VAT breakdown per clinic config
- [x] Settings page lets a clinic declare its own BIR compliance fields
- [x] `pnpm run ci:quality` green
