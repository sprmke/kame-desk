# Phase 39: Interactive odontogram / dental charting module

**Status:** Done
**Depends on:** Phase 7
**Unlocks:** —

**Plan reference:** `docs/workflow/planned/clinic-software-market-research-feature-gaps.md` §4.2 #6

## Production defaults (resolves plan §5 open decision 2)

- Dental becomes a real first-class charting surface (not just a SOAP template line), matching how dedicated dental PM systems (Dentrix, Curve, Open Dental) treat it, per the decision to build the full research backlog. Scope: adult permanent dentition (32-tooth) interactive odontogram with per-tooth/per-surface condition marking and a treatment-plan overlay tied to procedure line items on the existing invoice/billing model. Primary (deciduous) dentition and full periodontal charting (pocket depths, bleeding indices) are explicitly out of scope for this phase — flag as a future sub-phase if dental becomes a larger share of the pilot clinic base.

## Goal

A dentist can chart tooth-by-tooth condition and treatment on a visual odontogram during a consult, and a charted procedure flows into the visit's invoice as a line item instead of being re-typed.

## Tasks

### Backend

- [x] `ToothChartEntry` model + migration: `clinic_id`, `patient_id`, `soap_note_id`, `tooth_number` (FDI or universal numbering, pick one and document it), `surface` (nullable — mesial/distal/occlusal/buccal/lingual), `condition` (`caries`/`filled`/`missing`/`crown`/`root_canal`/`extraction_planned`/etc.), `status` (`existing`/`planned`/`completed`), `procedure_code`, `noted_at`
- [x] Link a `planned`→`completed` tooth entry to an `InvoiceLineItem` (optional FK) so charting a procedure can generate the corresponding billing line
- [x] `activity_log`: `tooth_chart.updated`

### Frontend

- [x] Odontogram component (SVG tooth map, 32-tooth adult layout) inside the SOAP note editor for dental-specialty visits
- [x] Click a tooth/surface → condition picker → adds a chart entry; visual color-coding by condition/status
- [x] Treatment plan view: list of `planned` entries with "Add to invoice" action per entry
- [x] Chart history view: prior visits' tooth entries overlaid/toggle-able for progression tracking

## Edge cases

- Same tooth charted in multiple visits (progression: caries → filled → crown) → history is additive, never overwrites prior entries; current-state view shows the latest `noted_at` per tooth/surface
- Non-dental specialty clinic → odontogram component only renders when the clinic/doctor specialty is dental (existing specialty-template mechanism from Phase 7), not shown by default
- Tooth marked `missing` → subsequent surface-level entries on that tooth are blocked in the UI (a missing tooth has no surfaces to chart)

## Docs to update

- [x] `docs/mvp.md` §6.5 (Consultation Records) — dental gets a real charting module, not just a template line
- [x] `docs/architecture/data-model.md` — `tooth_chart_entries`
- [x] `docs/guides/routes/dashboard/appointments/soap.md`

## Design notes (judgment calls not spelled out in the plan)

- `tooth_chart_entries.appointment_id` and `.soap_note_id` are both **nullable**, a deliberate deviation from reading the field list literally: charting happens live during a visit, often before the SOAP note's first save, so requiring a saved `soap_note_id` first would add friction with no clinical benefit. The chart is patient-level running history (like `patient_vitals`), not a per-visit snapshot — same reasoning `clinical_orders` already uses.
- `tooth_number` is validated server-side against the actual set of valid FDI adult codes (11-18, 21-28, 31-38, 41-48), not just a numeric range — a naive `11 <= n <= 48` range would silently accept invalid codes like 19, 20, 29, 30.
- "Add to invoice" reuses an existing draft invoice for the same appointment when one exists (checked by `patient_id` + `clinic_id` + `status=draft` + matching `appointment_id`), otherwise creates a new draft — so charting several planned procedures across one visit doesn't spawn a separate invoice per tooth.
- RBAC reuses the existing SOAP gates as-is (`assert_soap_read` / `assert_clinical_notes_write`) rather than inventing a new permission tier, since a tooth chart is clinical content at the same sensitivity level as a SOAP note.

## Hardening pass (post-implementation review)

A follow-up review of the shipped implementation found and fixed three real edge cases before sign-off:

- **Draft-invoice mismatch**: the original "add to invoice" reuse lookup fell back to "any draft invoice for this patient" whenever no `appointment_id` was known, which could silently attach a procedure to an unrelated older draft. Fixed to only reuse a draft when an `appointment_id` is actually known; otherwise it always creates a fresh draft. Covered by `test_tooth_chart_add_to_invoice_without_appointment_never_reuses_unrelated_draft`.
- **Dangling reference on line-item delete**: `tooth_chart_entries.invoice_line_item_id` had no `ondelete` clause, so deleting an invoice line item that a chart entry pointed at (a real, reachable path — `DELETE /invoices/{id}/line-items/{item_id}`) would raise a Postgres FK violation and fail the delete. Fixed with `ON DELETE SET NULL` (migration `040_tooth_chart_fk_ondelete`) plus explicit service-layer logic in `invoice_service.delete_line_item` that reverts the entry to `status="planned"` so it reappears on the treatment plan instead of being stuck `completed` with no invoice line behind it. Covered by `test_tooth_chart_entry_reverts_to_planned_when_invoice_line_item_deleted`.
- **Racy "find the new line item" lookup**: `add_entry_to_invoice` re-queried the DB for the line item with the highest `sort_order` after creating/appending it, a narrow window where a concurrent write to the same draft could return the wrong item. Replaced with picking the max `sort_order` from the `Invoice.line_items` already returned by `create_invoice`/`add_line_item`, removing both the extra round trip and the race.
- Also replaced the standalone `patient_id` index with a composite `(patient_id, noted_at DESC)` index matching the actual list-query shape.
- **Double-billing race**: `add_entry_to_invoice` read-then-wrote the entry's `status` with no locking, so two concurrent requests for the same entry (a retried request, a double-tap) could both observe `status="planned"` and each create an invoice line — double-billing the same procedure. Fixed with `.with_for_update()` on the entry lookup, the same row-locking pattern already used for clinic-level idempotency elsewhere in `invoice_service.py`.

## Bugs found during live-browser verification

Per this repo's requirement to exercise UI changes in a real browser: booked a live appointment, switched the SOAP template to Dental, charted a tooth (occlusal caries on 16), confirmed the tooth button colored red and the entry persisted after a page reload. No new bugs were found in this phase's own code. No pre-existing unrelated bugs were hit either (unlike Phases 37/38, where live testing surfaced real bugs in adjacent code).

## Exit criteria

- [x] Dentist can chart a tooth condition visually and it persists across visits as history
- [x] A planned procedure can be pushed to the invoice without re-typing it
- [x] `pnpm run ci:quality` green
