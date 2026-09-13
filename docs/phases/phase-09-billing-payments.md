# Phase 9: Billing & payments

**Status:** Done
**Depends on:** Phase 8
**Unlocks:** Phase 10

**mvp.md reference:** §6.7 · Gap closed: #11 in §7

## Goal

A clinic can know exactly who owes what: itemized invoices per visit, manual payment recording (cash/GCash/card/bank transfer — no live payment gateway required for MVP), partial payments and balance tracking, HMO claim notes, sequential receipt numbering, and revenue reporting feeding the dashboard.

## Prerequisites

- Phase 8 done (prescriptions can be a billable line item, though billing works standalone for visits without an Rx too)

## Tasks

### 1. Database

- [ ] `invoices` table — id, clinic_id, patient_id, appointment_id (nullable), invoice_number (sequential per clinic, configurable format — see BIR OR numbering note below), status (`draft`/`issued`/`partially_paid`/`paid`/`void`), subtotal, total, created_at, created_by_user_id
- [ ] `invoice_line_items` table — invoice_id, description, category (`consultation`/`procedure`/`lab`/`medicine`/`other`), quantity, unit_price, amount, hmo_covered_amount (nullable), hmo_claim_reference (nullable)
- [ ] `payments` table — invoice_id, method (`cash`/`gcash`/`card`/`bank_transfer`), amount, paid_at, reference_number (nullable), recorded_by_user_id
- [ ] `clinics.receipt_numbering_config` (jsonb: prefix, next_number, format) — configurable to match local requirements (mvp.md §6.7 calls out BIR Official Receipt numbering for the Philippines explicitly) — resolve `mvp.md` §15 open question #1 (target market) before finalizing the default format; if unresolved, ship a generic sequential default that's trivially reconfigurable, don't hardcode BIR-specific rules into logic that assumes they're universal

### 2. Backend

- [ ] `POST /api/v1/patients/{id}/invoices` — create from a visit (auto-suggests consultation fee from the doctor's profile, Phase 2) or standalone
- [ ] `POST /api/v1/invoices/{id}/line-items`, `PATCH/DELETE .../line-items/{item_id}` — while in `draft` status only; issuing locks line items the same way SOAP/Rx lock on finalize
- [ ] `POST /api/v1/invoices/{id}/issue` — assigns the next sequential invoice/receipt number (must be safe under concurrency — use a DB sequence or `SELECT ... FOR UPDATE` on the clinic's counter row, never a read-then-increment race)
- [ ] `POST /api/v1/invoices/{id}/payments` — records a payment, recalculates status (`partially_paid` vs `paid` based on sum of payments vs. total)
- [ ] `POST /api/v1/invoices/{id}/void` — reason required, never deletes
- [ ] `GET /api/v1/patients/{id}/balance` — outstanding balance across all invoices (this becomes `check_patient_balance`, a Tier 0 AI tool later per mvp.md §9.5 — build as a clean reusable service function)
- [ ] `GET /api/v1/clinics/{id}/outstanding-balances` — sortable/exportable list (feeds Phase 12 reporting and the dashboard widget from §6.2)
- [ ] `GET /api/v1/invoices/{id}/receipt-pdf` — uses the shared PDF pipeline from Phase 7

### 3. Frontend

- [ ] `src/features/billing/` — invoice builder (add line items, fee picker sourced from Phase 2's `service_fees`), payment recording dialog, balance view per patient
- [ ] Dashboard widgets: revenue summary (today/week/month) and outstanding balance list (§6.2) — first real dashboard widgets wired to real data
- [ ] Receipt print/PDF view

## Data model

New: `invoices`, `invoice_line_items`, `payments`. Extended: `clinics` (receipt numbering config).

## API endpoints

| Method            | Path                                        | Roles                                                                     |
| ----------------- | ------------------------------------------- | ------------------------------------------------------------------------- |
| POST/GET          | `/api/v1/patients/{id}/invoices`            | owner, admin, reception (full) · doctor (view own visits only, per §6.11) |
| POST/PATCH/DELETE | `.../line-items`                            | owner, admin, reception                                                   |
| POST              | `/api/v1/invoices/{id}/issue`               | owner, admin, reception                                                   |
| POST              | `/api/v1/invoices/{id}/payments`            | owner, admin, reception                                                   |
| POST              | `/api/v1/invoices/{id}/void`                | owner, admin                                                              |
| GET               | `/api/v1/patients/{id}/balance`             | owner, admin, doctor, reception                                           |
| GET               | `/api/v1/clinics/{id}/outstanding-balances` | owner, admin                                                              |

## Edge cases & safety

- Sequential receipt numbering must never produce a gap-free-but-duplicate number under concurrent issues — this is a common audit-failure point; test explicitly with concurrent issue requests.
- A doctor's "view own visits only" billing permission (§6.11: "View own visits" for Doctor role) must be enforced server-side — a doctor querying another doctor's invoice by ID must get a 403, not a 404-that-leaks-existence or a silent 200.
- Partial payments summing to exactly the total must flip status to `paid`, not linger at `partially_paid` due to a floating-point rounding issue — use integer cents or `Decimal`, never `float`, for all money fields.
- Voiding an invoice that already has recorded payments needs a clear product decision (recommend: block void if payments exist; require voiding/refunding payments first) — document the chosen rule.
- HMO claim notes are structured but non-live (§6.7: "MVP tracks this as structured notes, not a live EDI integration") — don't let the UI imply a live claim status that doesn't exist.

## Testing

- pytest: concurrent invoice-numbering safety, partial-payment-to-paid transition with Decimal math, doctor own-visits-only enforcement, void-with-payments rule
- Vitest: invoice builder line-item math, payment form validation
- Playwright: full visit-to-payment flow — book → consult → bill → pay → verify balance is zero

## Docs to update in this phase

- `docs/architecture/data-model.md` — billing schema, money-type convention (Decimal/cents) stated explicitly as a repo-wide rule
- `docs/guides/routes/dashboard/billing/*.md`
- `mvp.md` §15 open question #1 (compliance/receipt-numbering market) and #2 (on-site medicine dispensing, which would need an inventory-lite line item sooner) — resolve or explicitly re-flag as still open

## Exit criteria

- [x] Itemized invoices, partial payments, and balance tracking work end-to-end
- [x] Receipt numbering is safe under concurrency (tested)
- [x] Dashboard revenue/balance widgets show real data
- [x] `pnpm run ci:quality` green (API pytest + web vitest/build)
