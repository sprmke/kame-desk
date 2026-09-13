# Phase 17: AI safety checks on prescriptions + AI billing/receipt assist

**Status:** Done
**Depends on:** Phase 16
**Unlocks:** Phase 18

**mvp.md reference:** §8.6 (AI explanation layer only — the deterministic check already shipped in Phase 8), §8.7

## Goal

Two focused AI additions layered on already-shipped deterministic systems: (1) plain-language explanations of allergy/drug-interaction flags from Phase 8's deterministic checker, and (2) AI-assisted extraction from a submitted receipt/HMO document to pre-fill a billing entry, with staff always confirming before it's finalized.

## Prerequisites

- Phase 16 done (this phase reuses the assistant's tool/confirm infrastructure rather than building a parallel one)
- Phase 8 (prescriptions + deterministic checker) and Phase 9 (billing) done

## Tasks

### 1. AI explanation for prescription safety flags (§8.6)

- [ ] `explain_safety_flag` — a small PydanticAI call that takes a _already-computed_ deterministic flag (from Phase 8's `check_allergy_interaction_conflicts`) and produces a plain-language explanation for the doctor — **the AI never decides whether to block; the deterministic check already made that decision in Phase 8, this phase only adds an explanation layer on top of an unchanged decision**
- [ ] Wire this into Phase 8's Rx pad UI: when a flag appears, an "explain" affordance calls this endpoint and shows the plain-language text alongside the existing structured flag data (drug names, reaction type) — the structured data remains the doctor's primary signal, the AI text is supplementary
- [ ] This is a Tier 0 (read-only, explanatory) capability — it never touches the override/write path from Phase 8, which is unchanged by this phase

### 2. AI billing/receipt assist (§8.7)

- [ ] `POST /api/v1/patients/{id}/billing-assist/extract` — accepts an uploaded receipt/HMO letter image or PDF (via `markitdown`-equivalent extraction for text-bearing documents, or a vision-capable model call for image receipts), returns extracted `{amount, date, provider, reference_number}` as a structured, editable draft — **never writes a billing record directly**
- [ ] Frontend: staff reviews/edits the extracted fields, then submits through Phase 9's normal `POST .../invoices/{id}/payments` or `.../line-items` endpoint — the AI extraction is purely a data-entry accelerant feeding an unchanged, already-safe write path
- [ ] Same PHI-minimization and no-raw-content-logging rules as every other AI feature apply to whatever document content is sent to the extraction model

## Data model

No new tables required if extraction results are ephemeral (returned to the client, not persisted until the human submits the real invoice/payment write). If audit requirements call for persisting extraction attempts, add a lightweight `billing_extraction_attempts` table (patient_id, source_file_r2_key, extracted_data jsonb, confirmed boolean, created_at) — decide based on whether the clinic needs to trace "the AI suggested X, staff entered Y" for dispute resolution; recommend yes, for the same audit-trail spirit as everything else in this product.

## API endpoints

| Method | Path                                           | Roles                   |
| ------ | ---------------------------------------------- | ----------------------- |
| POST   | `/api/v1/prescriptions/{id}/explain-flag`      | doctor, owner           |
| POST   | `/api/v1/patients/{id}/billing-assist/extract` | owner, admin, reception |

## Edge cases & safety

- The explanation endpoint must never be able to _change_ the underlying flag's severity or block/allow decision — it consumes the already-computed result, it doesn't recompute it with different logic.
- Billing extraction must handle a garbled/unreadable document gracefully (partial extraction, clearly marked low-confidence fields) rather than confidently hallucinating a plausible-looking but wrong amount — every extracted field should be easy for staff to spot-check against the original document image shown alongside it.
- Never finalize a financial record from AI extraction without the explicit staff confirm step that was already required by Phase 9's invoice/payment endpoints — this phase adds no new unconfirmed write path.
- Receipt/HMO documents may contain the patient's own PHI (their name, insurer, sometimes diagnosis codes on an HMO letter) — apply the same minimization/logging rules as clinical AI features.

## Testing

- pytest: explanation endpoint never alters the Phase 8 flag decision (regression test pinning that behavior), extraction returns structured output for a fixture document, extraction never writes a payment/invoice row directly
- Vitest: Rx pad "explain" affordance, billing-assist review-and-edit UI
- Manual QA: run extraction against a deliberately low-quality scanned receipt, confirm the UI surfaces uncertainty rather than false confidence

## Docs to update in this phase

- `docs/architecture/ai-clinic-assistant.md` — add these two capabilities to the shipped-features section, note explicitly that neither is a Tier 1/2 write tool in the assistant's own tool catalog (they're standalone AI-assist endpoints, not chat tools, unless a later iteration wires them into the assistant's tool catalog — if so, update `mvp.md` §9.5's table too)

## Exit criteria

- [ ] Prescription flag explanations are accurate to the underlying deterministic result and never override it
- [ ] Billing extraction produces a reviewable, editable draft that never bypasses Phase 9's confirmed-write path
- [ ] `pnpm run ci:quality` green
