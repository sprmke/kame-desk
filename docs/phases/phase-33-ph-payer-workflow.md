# Phase 33: PH payer workflow — HMO eligibility, LOA, PhilHealth e-claims path

**Status:** Done
**Depends on:** Phase 26
**Unlocks:** —

**Plan reference:** `docs/workflow/planned/clinic-software-market-research-feature-gaps.md` §4.1 #1, #2, #6

## Production defaults (resolves plan §5 open decisions 3 and 6)

- kame-desk does not pursue its own PhilHealth HITP / BIR CAS certification for MVP. Claims/eligibility submission is built behind a pluggable `claims_partner` adapter interface. MVP ships a `manual` adapter (staff-entered reference numbers, status tracked in-app); a real HITP API adapter can be added later without changing the data model or UI.
- This is a new phase set, not folded into the (already-Done) Phase 20–32 rebuild — tracked separately per plan §5.6.
- Eligibility checks and LOA requests are structured, trackable entities — not free-text notes on a claim.

## Goal

Front desk can verify a patient's HMO/PhilHealth coverage before a visit, submit an LOA request and track its status without a phone call, and every insurance claim carries a payer type so PhilHealth claims are distinguishable from private HMO claims.

## Tasks

### Backend

- [x] `EligibilityCheck` model + migration: `clinic_id`, `patient_id`, `payer_name`, `payer_type` (`hmo`/`philhealth`), `member_id`, `status` (`pending`/`verified`/`denied`/`expired`), `verified_amount`, `notes`, `checked_by_user_id`, timestamps
- [x] `LoaRequest` model + migration: `clinic_id`, `patient_id`, `claim_id` (nullable FK to `insurance_claims`), `hmo_name`, `status` (`requested`/`submitted`/`approved`/`denied`), `reference_number`, `document_object_key` (R2 upload), `requested_by_user_id`, `submitted_at`, `decided_at`, `decision_notes`
- [x] Extend `InsuranceClaim`: add `payer_type` (`hmo`/`philhealth`/`self_pay`/`other`), `loa_request_id` (nullable FK)
- [x] `app/services/claims_partner.py` — adapter protocol (`submit_eligibility_check`, `submit_loa_request`, `submit_claim`) + `ManualClaimsPartner` implementation (marks as submitted, awaits staff-entered reference/decision)
- [x] `app/services/eligibility_service.py`, `app/services/loa_service.py` — CRUD + status transitions, RBAC via existing `assert_billing_read`/write pattern
- [x] Routers: `eligibility_checks.py`, `loa_requests.py` mounted under `/api/v1`
- [x] `activity_log` events: `eligibility_check.created`, `eligibility_check.updated`, `loa_request.created`, `loa_request.status_changed`
- [x] Payer directory: simple clinic-scoped list of known HMO/PhilHealth payer names (settings-managed, reused by claim/eligibility/LOA forms)

### Frontend

- [x] Eligibility check panel on patient detail + booking flow: request check, show status/verified amount (`PatientEligibilityCard`, mounted on `PatientDetailPage` and `AppointmentNewPage`)
- [x] LOA requests: create request, status timeline (requested → submitted → approved/denied). Now its own Billing hub tab (`LoaRequestsPage`). Document upload deferred — `document_object_key` field exists on the model but no upload UI yet; not required for the timeline/status workflow to be useful.
- [x] Claim form: payer type selector (HMO / PhilHealth / self-pay / other), link to an LOA request
- [x] Payer directory management (add/edit HMO/PhilHealth names) — now at Settings → Clinic → Payers (`PayersSettingsPage`)
- [x] Claims list: filter by payer type

**Superseded layout note:** this phase originally shipped all four surfaces as stacked cards on `/dashboard/billing/claims`, each card holding an inline create form above its own list (`ClaimsSection`, `EligibilitySection`, `LoaSection`, `PayerDirectorySection`). That was later split into route-based Billing hub tabs (`Invoices · Claims · Eligibility · LOA`) with create actions moved into `ResponsiveModal` dialogs opened from `SectionHeaderActions`, and the payer directory moved to Settings. Eligibility and LOA list endpoints gained `q` / `page` / `page_size` / `sort` so their pages can use the shared `ManagedList` chrome like every other clinic list.

### AI assistant

- [x] Tier 0 read-only tool `check_eligibility_status` (reads existing `EligibilityCheck` records only — no live insurer call in MVP) — added to `docs/architecture/ai-clinic-assistant.md` tool catalog

## Edge cases

- Eligibility check with no matching payer in directory → allow free-text payer name, do not block
- LOA request with no linked claim yet (checked before invoice exists) → allow standalone creation from the LOA requests panel; `PATCH /loa-requests/{id}` accepts `claim_id` to link it once a claim exists, validated against the same patient (`test_loa_request_can_link_claim_after_creation`, `test_loa_request_link_rejects_mismatched_patient_claim`)
- Denied LOA → claim stays payable as self-pay, invoice not blocked
- Duplicate eligibility check same-day for same patient/payer → allowed, list shows history (coverage can change)

## Docs to update

- [x] `docs/mvp.md` §6.7 (billing) — replace "HMO/insurance claims as a clinic-wide status list" note with eligibility/LOA workflow description
- [x] `docs/architecture/data-model.md` — new tables
- [x] `docs/architecture/ai-clinic-assistant.md` — new tool
- [x] `docs/guides/routes/dashboard/billing/claims.md`, `docs/guides/routes/dashboard/patients/detail.md`, `docs/guides/routes/dashboard/appointments/new.md`
- [x] Post-split guides: `docs/guides/routes/dashboard/billing/eligibility.md`, `.../billing/loa.md`, `.../settings/payers.md`, plus `docs/architecture/api-conventions.md` § payer workflow endpoints

## Exit criteria

- [x] Front desk can request and see eligibility status without leaving the product
- [x] LOA request has a visible status timeline from request to decision
- [x] Claims are filterable by payer type
- [x] `pnpm run ci:quality` green
