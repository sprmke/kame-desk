# Phase 26: Billing integrity

**Status:** Done
**Depends on:** Phase 25
**Unlocks:** Phase 27, Phase 31

**Plan reference:** `docs/workflow/planned/ground-up-app-redesign-and-platform-admin.md` §4 Phase 26

## Production defaults

- BIR Official Receipt numbering stays `OR-` / next `1` / pad `6` (Phase 22). Credit notes use prefix `CN-` with the same pad width and a separate counter on `clinics.receipt_numbering_config.credit_next_number`.
- A paid invoice is never voided. Corrections use a credit note (refund or adjustment) with a required reason.
- HMO claims are clinic-tracked status records (`draft` / `submitted` / `approved` / `denied` / `paid`). No live insurer EDI.

## Goal

Front desk can see every unpaid invoice clinic-wide, fix a billing mistake after payment, and track HMO claims without leaving the product.

## Tasks

### Backend

- [x] Credit note / refund against a paid or partially paid invoice
- [x] Clinic-wide invoice list with status/date/patient filters and CSV export
- [x] Insurance claims table + CRUD/status

### Frontend

- [x] Top-level Billing nav: Invoices, Claims
- [x] Documents nav: Generate + Templates
- [x] Clinic-wide invoice list + outstanding
- [x] Credit note action on invoice detail
- [x] Claims list + status

## Exit criteria

- [x] Staff can answer who owes money clinic-wide
- [x] A paid invoice can be corrected without void
- [x] Tests + type-check green
