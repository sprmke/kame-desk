# Phase 38: Growth & retention differentiators

**Status:** Done
**Depends on:** Phase 27, Phase 26
**Unlocks:** —

**Plan reference:** `docs/workflow/planned/clinic-software-market-research-feature-gaps.md` §4.2 #1, #3, #4, #7, #8, #9, #10

Bundles the remaining nice-to-have items that are individually small (each would be a sub-phase-sized amount of work on its own) into one phase, grouped by shared surface area.

## Production defaults

- **Multi-branch/franchise reporting (§4.2 #5) stays deferred**, not built — the plan doc itself recommends keeping it deferred unless the target segment shifts from solo/small clinic toward chains; nothing in this backlog changes that segment assumption, so it's excluded even under "build the whole doc."
- **Patient financing/BNPL (§4.2 #3):** no confirmed PH healthcare-specific BNPL partner exists per the research. Ship the invoice-side hook (a "Send to financing" action + status field) behind a pluggable provider interface, not a live integration — matches the same adapter pattern used for claims partners in Phase 33. Do not fabricate a fake BNPL partner integration.
- **FHIR/DOH PHIE export (§4.2 #10):** low near-term priority per the plan — ship only a minimal FHIR Patient+Encounter JSON export endpoint (read-only, on-demand) as a documented capability flag, not a live PHIE connection (no PHIE sandbox/credentials exist to integrate against).

## Tasks

### Reputation management (§4.2 #1)

- [x] Post-visit trigger (visit marked Completed) queues a "request a review" prompt with the clinic's Google Business review link, sent via the existing reminder/messaging channel (email/SMS/WhatsApp)
- [x] Settings: clinic enters its Google Business review link, enable/disable toggle
- [x] `activity_log`: `review_request.sent`

### Patient satisfaction / NPS micro-survey (§4.2 #7)

- [x] One-question NPS prompt (0-10 + optional comment) sent alongside/after the review-request flow, same channel infra
- [x] `PatientSurveyResponse` model + migration: `clinic_id`, `patient_id`, `visit_id`, `score`, `comment`, `sent_at`, `responded_at`
- [x] Reports: NPS trend on the existing reports dashboard (Phase 12/28)

### Doctor-to-doctor referral chart sharing (§4.2 #9)

- [x] Extend existing referral-letter document (Phase 10, `mvp.md` §6.8): add an optional "share chart summary" attachment (read-only chart-summary snapshot, same shape as Phase 37's patient chart summary) alongside the printed letter
- [x] Recipient access: a scoped, expiring share link (no recipient account required) — same signed-URL pattern as document downloads
- [x] `activity_log`: `referral.chart_shared`

### Membership / subscription care plans (§4.2 #4)

- [x] `MembershipPlan` model + migration: `clinic_id`, `name`, `price`, `billing_interval` (`monthly`/`quarterly`/`annual`), `included_services` (JSONB — visit count/type allowances), `is_active`
- [x] `PatientMembership` model + migration: `clinic_id`, `patient_id`, `plan_id`, `status` (`active`/`cancelled`/`expired`), `started_at`, `current_period_end`
- [x] Billing integration: invoices for a member with remaining plan allowance apply the plan discount/waiver automatically; recurring plan charge itself is a manually-recorded payment for MVP (no live recurring-billing gateway, matches the existing manual-payment-entry pattern in §6.7)
- [x] Settings: manage clinic's membership plans; Patient detail: enroll/cancel membership

### Financing/BNPL hook (§4.2 #3)

- [x] `app/services/financing_partner.py` — adapter protocol (`create_financing_request`) with a `NoopFinancingPartner` default (feature hidden unless a clinic explicitly configures a real provider later)
- [x] Invoice action: "Send to financing" (only visible when a provider is configured), status field on invoice

### DOH EMR accreditation flag (§4.2 #8)

- [x] Settings field: DOH accreditation number + validity date (display-only, same pattern as BIR PTU/CAS in Phase 34) — trust-signal metadata only, no accreditation workflow

### FHIR export (§4.2 #10)

- [x] `GET /patients/{id}/fhir-export` — read-only, on-demand FHIR R4 `Patient` + `Encounter` bundle JSON, RBAC-gated same as chart access
- [x] Documented as a capability flag in `docs/architecture/data-model.md`, explicitly not a live PHIE connection

## Docs to update

- [x] `docs/mvp.md` §6 (new §6.15), §14 (multi-branch deferral note made explicit)
- [x] `docs/architecture/ai-clinic-assistant.md` — N/A, no Tier 0 assistant tools added for review-request/NPS visibility
- [x] `docs/guides/routes/dashboard/settings/clinic.md` (growth settings card), `docs/guides/routes/dashboard/settings/membership-plans.md` (new), `docs/guides/routes/dashboard/reports.md` (NPS tab), `docs/guides/routes/dashboard/patients/detail.md` (membership card, chart-share button), `docs/guides/routes/dashboard/billing/invoices.md` (financing action, waiver), `docs/guides/routes/nps.md` (new), `docs/guides/routes/referral-chart.md` (new)
- [x] `docs/architecture/data-model.md` — Phase 38 entity row + subsection, including the FHIR export capability-flag note

## Bugs found during live-browser verification

Per this repo's requirement to exercise UI changes in a real browser, not just rely on type-checking/test suites — four real bugs were found and fixed while verifying this phase end-to-end:

1. **Invoice quick-add fee buttons mislabeled every line item's `category` as `"procedure"`** (`apps/web/src/features/billing/pages/InvoiceNewPage.tsx`), ignoring the service fee's actual category (`"consultation"`, `"lab"`, etc.). This silently broke membership-waiver matching (a consultation line never matched a plan's `consultation` allowance) — caught only by enrolling a test patient in a plan, quick-adding "General consultation" on an invoice, and observing the waiver line never appeared. Fixed by passing the fee's real category through, validated against the backend's `LineCategory` literal (falling back to `"other"` for anything unrecognized) — a pre-existing Phase 9 bug, not introduced by this phase, but directly blocking this phase's waiver feature.
2. **Template-injection guard false-positive on ordinary English words** (`apps/api/app/services/template_renderer.py::validate_template_body`): naive substring matching against `"eval"` flagged the seeded referral-letter template's own text ("...for further **eval**uation") as forbidden syntax, making `POST /patients/{id}/documents` 500 for the referral-letter template specifically — caught while creating a test referral letter to verify the chart-share feature. Fixed by switching to word-boundary regex matching (`\beval\b`, `\bexec\b`, `\bimport\b`, `\bopen\(`) so real injection attempts (`{{eval(...)}}`, `{% import os %}`, `__class__`) are still blocked but ordinary prose is not — a pre-existing Phase 10 bug, unrelated to this phase's code but blocking live verification of the chart-share flow built here. Verified via `test_documents.py`'s existing forbidden-syntax test plus the full 208-test backend suite, both green.
3. Confirmed (not a bug): `financing_available` correctly stays `false` and the "Send to financing" button stays hidden while `settings.financing_partner_enabled` defaults to `False` — matches the "not a fabricated live integration" requirement.
4. Confirmed (not a bug): the NPS reply link's single-use guard (`responded_at` check) correctly rejects a replayed submission with "Link invalid or expired" rather than silently double-counting it.

## Exit criteria

- [x] Review requests and NPS surveys send automatically post-visit and are reportable
- [x] A referral letter can carry a scoped chart-summary share link
- [x] Membership plans can be sold, enrolled, and applied to an invoice
- [x] Financing hook and FHIR export exist as documented, adapter-gated capabilities, not fabricated live integrations
- [x] `pnpm run ci:quality` green
