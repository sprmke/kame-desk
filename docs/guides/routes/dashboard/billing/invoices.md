# Billing — invoices & payments

**Status:** Documented  
**Route:** `/dashboard/billing/invoices`, `/dashboard/patients/:patientId/invoices/new`, `/dashboard/patients/:patientId/invoices/:invoiceId`  
**Dashboard widgets:** `/dashboard` shows month revenue (with today/week), outstanding balances, and open claims. See [dashboard/index.md](../index.md).

## Behavior

- The **Billing** title sits above the Invoices / Claims tabs; the billing content renders below the tabs. **Export** is contributed to the section header by this tab. Switching tabs changes only the content, never the title.
- Reception/admin/owner create draft invoices per patient, optionally linked to an appointment. Line descriptions use a shared placeholder.
- When created with an appointment and no line items, a consultation line is suggested from the appointment doctor's `consultation_fee`.
- Service fees from clinic settings can be picked in the invoice builder UI.
- Receipt/HMO upload on new invoice uses a document dropzone, then `POST /api/v1/patients/{id}/billing-assist/extract` (editable draft only; staff confirms via normal issue/payment endpoints).
- Issue assigns the next sequential receipt number (`clinics.receipt_numbering_config`: `prefix`, `next_number`, `pad_width`) under `SELECT FOR UPDATE` on the clinic row.
- Line items are editable only while status is `draft`. Issue locks items and generates a receipt PDF in R2.
- Payments (cash, GCash, card, bank transfer) can be partial. Status becomes `partially_paid` or `paid` using `Decimal` math. **Pay** uses `ResponsiveModal` (bottom sheet below `lg`).
- Void requires owner/admin, a reason, and **no recorded payments**.
- After payment, owner/admin issue a **credit note** (`refund` or `adjustment`) with a reason. Paid invoices are never voided. Credit numbers use `CN-` and `receipt_numbering_config.credit_next_number`.
- Clinic-wide invoice list at **Billing → Invoices**: live search, status filter, sort, per-page, Table / List views, CSV export, outstanding total. Amounts use tabular numerals. Payment state uses shape + label (`PaymentStatus`), not pastel-only badges. Loading uses a list skeleton; no results use `EmptyState` in the same card as the table (distinct copy when filters are active). Query params: `q`, `status`, `from`, `to`, `page`, `limit`, `sort`, `view`. The Filters popover holds one date-range picker (start click, then end click) that writes both `from` and `to`; it counts as a single active filter.
- Doctors may list/view invoices only for their own visits (appointment `doctor_id` match). Other roles see all clinic invoices for the patient.
- Receipt/invoice PDF (`app/services/invoice_pdf.py`) renders the clinic's `bir_compliance_config` (Phase 34): TIN, registered business name/address (falls back to the plain clinic profile fields when unset), PTU/CAS accreditation number, and either a VAT breakdown (vatable sales / 12% VAT) when VAT-registered or a "Non-VAT" disclosure line when not.
- A non-blocking banner appears at the top of the invoice list when the clinic's `bir_compliance` is incomplete (no TIN, a PTU/CAS mode with no accreditation number, or an expired accreditation date), pointing staff to Settings → Clinic to fix it. It never blocks invoice creation or issuance.
- **Send to financing** (Phase 38): a button on a non-draft invoice detail page, visible only when `settings.financing_partner_enabled` is on (off by default, no confirmed PH healthcare BNPL partner exists yet). Once sent, a status line replaces the button showing `financing_status`. Backed by a pluggable `FinancingPartner` adapter (`app/services/financing_partner.py`) with a `NoopFinancingPartner` default. The hook is real, but does nothing until a clinic configures an actual provider.
- Membership-plan patients get an automatic waiver line ("Membership benefit (\<plan name\>)") added to a matching-category line item when creating an invoice, if their plan still has allowance left this period (Phase 38, `docs/guides/routes/dashboard/settings/membership-plans.md`).

## Save paths

| UI action               | API                                                                 | DB effect                                                                           |
| ----------------------- | ------------------------------------------------------------------- | ----------------------------------------------------------------------------------- |
| New invoice → Issue     | `POST /patients/{id}/invoices` then `POST /invoices/{id}/issue`     | `invoices`, `invoice_line_items`, increments `receipt_numbering_config`, PDF upload |
| Receipt extract (draft) | `POST /patients/{id}/billing-assist/extract`                        | `billing_extraction_attempts` audit row only; no invoice write                      |
| Record payment          | `POST /invoices/{id}/payments`                                      | `payments` row; invoice status recalculated                                         |
| Void                    | `POST /invoices/{id}/void`                                          | `status=void`, `void_reason`, `voided_at`                                           |
| Credit note             | `POST /invoices/{id}/credit-notes`                                  | `credit_notes` row; increments `credit_next_number`                                 |
| Send to financing       | `POST /invoices/{id}/send-to-financing`                             | sets `invoices.financing_status`                                                    |
| Clinic invoices         | `GET /invoices` (`q`, `status`, dates, `page`, `page_size`, `sort`) | clinic-scoped list                                                                  |
| Export                  | `GET /invoices/export`                                              | CSV                                                                                 |
| Patient balance         | `GET /patients/{id}/balance`                                        | read aggregate                                                                      |
| Dashboard revenue       | `GET /clinics/{id}/revenue-summary`                                 | sum of `payments` by period                                                         |
| Outstanding list        | `GET /clinics/{id}/outstanding-balances`                            | aggregate per patient                                                               |

## RBAC

| Role                    | Create/issue/pay | View            | Void                        |
| ----------------------- | ---------------- | --------------- | --------------------------- |
| owner, admin, reception | yes              | all             | owner/admin (void + credit) |
| doctor                  | no               | own visits only | no                          |

## AI assistant parity

Tier 0 `check_patient_balance` is planned in Phase 16; backend `get_patient_balance()` is the reusable service function.

## Edge cases

- Concurrent issue requests get unique numbers (tested).
- HMO line fields remain notes. Clinic-wide claim status lives on `/dashboard/billing/claims`.
- Void blocked when payments exist. Use a credit note instead.

## Implementation map

- API: `apps/api/app/routers/invoices.py`, `apps/api/app/services/invoice_service.py`, `apps/api/app/services/invoice_pdf.py`, `apps/api/app/services/financing_partner.py`, `apps/api/app/services/membership_service.py` (waiver)
- Web: `apps/web/src/features/billing/`, dashboard outstanding/revenue cards in `apps/web/src/features/dashboard/`
- Migration: `010_billing.py`, `031_bir_compliance_depth.py`

## Host-facing knowledge

Staff can bill a visit from the patient chart: open the patient, tap **Invoice**, add lines or use fee shortcuts, then **Issue**. Record payments on the invoice detail screen until balance is zero (on a phone, Pay opens a sheet from the bottom). Clinic-wide invoices live under **Billing → Invoices**: search, filter by status or date, sort, change page size, and switch Table or List. The dashboard shows today's revenue and who still owes money. Receipt numbers follow the clinic's OR prefix settings. Doctors only see bills for their own patients' visits. On a phone, open Dashboard from **More**. If the invoices page shows a compliance reminder banner, it means the clinic's TIN or BIR accreditation details are missing or expired in Settings → Clinic. Invoices still work normally; it is only a reminder.
