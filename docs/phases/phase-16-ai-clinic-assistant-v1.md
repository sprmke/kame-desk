# Phase 16: AI Clinic Assistant v1 (Tier 0 → Tier 1 → Tier 2)

**Status:** Done
**Depends on:** Phase 15
**Unlocks:** Phase 17

**mvp.md reference:** §8.1, §9 (full architecture spec — read it in full before starting, this phase file sequences it, does not restate every detail) · **This is the flagship feature and the highest-risk phase in the plan. Read `docs/architecture/ai-clinic-assistant.md` and `.cursor/rules/ai-assistant-safety.mdc` before writing a single tool.**

## Goal

Ship the chat panel that can answer questions and execute real dashboard actions, scoped strictly to the signed-in user's RBAC, with a server-computed three-tier risk model, full audit trail, and a staged rollout: **Tier 0 (read) first, then Tier 1 (auto-write), then Tier 2 (confirm-required write)** — exactly the order kame-homes used for its own dashboard assistant, because each tier is a smaller blast radius to get wrong than the next.

## Prerequisites

- Phases 1–15 all done — this phase's tools are thin wrappers around service functions every prior phase already built (patients, appointments, SOAP drafts, billing, chart search). If a tool needs a service function that doesn't cleanly exist yet, that's a signal a prior phase's service layer wasn't factored correctly — fix the service layer, don't duplicate logic inside a tool.
- Per-clinic AI usage cap (Phase 14) already exists and is proven to work
- Kill switch design decided (see Tasks)

## Sub-phases (ship and verify each before the next)

### 16a. Foundation: context model, tier classifier, safety checks (no tools registered yet)

- [ ] `app/ai/assistant/context.py` — resolves `pageContext` (current route's `patientId`/`appointmentId`/`visitId`) and `attachedContext[]` (composer-pinned items, max ~8) per mvp.md §9.2; implements the argument-resolution order: **explicit args in the message → attached context → ambient page context**
- [ ] `app/ai/assistant/tiers.py` — the server-computed tier classifier (never model-decided): base tier per tool + escalation rules:
  - Bulk escalation: 2+ writes requested in one turn → every one becomes Tier 2
  - Cross-scope escalation: acting outside current page context and outside pinned context → Tier 2
  - External-send escalation: any tool that sends a real message to a patient → always Tier 2, rendered with `EXTERNAL_SEND_TOOL_NAMES`-style distinct styling (mirror kame-homes' pattern name)
  - Clinical-write escalation: any SOAP/prescription/diagnosis write → always Tier 2, no exceptions, regardless of what the generic classifier would say
- [ ] `app/ai/assistant/safety.py`:
  1. Independent RBAC re-check per tool call — re-derive the permission from the original request's auth token, never from anything the model asserts
  2. Immediate pre-execution re-check against current DB state (e.g. appointment not already cancelled by someone else) — hard-fail on mismatch, never write over a stale assumption
  3. Post-generation grounding check — every fact stated (balance, date, status) is checked against real tool-result data before being shown; strip ungrounded claims, never fabricate a patient/balance/chart entry
  4. Full audit trail — every executed write (Tier 1 auto or Tier 2 confirmed) recorded to `activity_log` with `actor_type = 'ai_assistant'`
  5. Never-build list enforced at the tool-registration level — irreversible/maximal-blast-radius actions (delete a patient record, delete a chart version, bulk-message the entire patient list) are never registered as callable tools, full stop
  6. Cost control — reuse Phase 14's per-clinic daily cap, enforced before any model call
- [ ] `ai_assistant_conversations`, `ai_assistant_messages`, `ai_assistant_actions` tables (per `mvp.md` §11) — conversation/message history scoped per clinic/user; every Tier 1/Tier 2 executed action recorded here _and_ feeding `activity_log`
- [ ] Kill switch: a platform-wide config flag (env var or a `platform_settings` table) defaulting to **off**, plus a per-clinic `clinics.ai_assistant_enabled` toggle in Settings (§6.12) — both checked before any assistant request is served, no deploy needed to flip either

### 16b. Tier 0 tools (read-only, ship first)

- [ ] `search_patients`, `get_patient`, `list_appointments`, `get_available_slots` (reuse Phase 4's service function), `check_patient_balance` (reuse Phase 9's), `search_charts` (reuse Phase 15's), `draft_soap_note` (reuse Phase 14's drafting pipeline — produces a draft only, never writes)
- [ ] Every Tier 0 tool: RBAC re-check + grounding check wired in from day one, even though nothing writes yet — do not skip safety plumbing "because it's just a read," the pattern must be uniform before Tier 1/2 tools are added
- [ ] Ship to a small internal/pilot audience with the kill switch on by default per clinic, opt-in only

### 16c. Tier 1 tools (auto-executed, low blast radius)

- [ ] `mark_thread_read`-equivalent if applicable to this domain, `revoke_pending_staff_invite` (reuses Phase 2's revoke endpoint), plain forward-only appointment status moves with no financial/clinical impact (e.g. `Scheduled → Confirmed` with no reschedule)
- [ ] Verify each Tier 1 tool is genuinely idempotent (safe to call twice) before shipping — this is the defining property that makes auto-execution acceptable

### 16d. Tier 2 tools (confirm-required — the majority of writes)

- [ ] `propose_book_appointment`, `propose_reschedule_appointment` (Tier 1 for simple moves per §9.5, Tier 2 for same-day/short-notice — implement via the escalation rules in 16a, not a special case per tool), `propose_cancel_appointment` (always Tier 2), `propose_save_soap_note` (doctor-only, always Tier 2, creates a new chart version through the exact same Phase 7 service function a manual save uses), `propose_issue_prescription` (doctor-only, always Tier 2, runs Phase 8's allergy/interaction check first and surfaces any flag in the confirm card before the user can confirm), `propose_create_invoice_line` (always Tier 2), `propose_send_reminder` (always Tier 2 + external-send styling), `propose_generate_document` (always Tier 2, reuses Phase 10's template/render pipeline)
- [ ] Every Tier 2 tool returns a **proposal** — nothing writes until the user taps Confirm in the chat UI; confirming calls the exact same service function a manual dashboard action would call, through the same RBAC dependency

### 2. Backend (cross-cutting)

- [ ] `POST /api/v1/assistant/conversations/{id}/messages` (SSE response) — streams the assistant's turn: text, structured cards, tool calls, confirm cards
- [ ] `POST /api/v1/assistant/actions/{action_id}/confirm` — executes a pending Tier 2 proposal (re-runs every safety check in 16a immediately before writing, per point 2)
- [ ] `POST /api/v1/assistant/actions/{action_id}/cancel` — discards a pending proposal, no write occurs
- [ ] Structured logs for every AI tool call (tool name, tier, outcome) separate from `activity_log`, per `mvp.md` §10 Observability

### 3. Frontend

- [ ] `src/features/assistant/` — floating launcher (bottom-right, every dashboard screen, hidden from patients — staff/doctor tool only), chat panel with streaming text, structured cards (patient card, appointment card, invoice card — a `ChatBlock`-equivalent component library adapted from kame-homes' pattern), confirm/cancel cards for Tier 2 actions
- [ ] Quick-action suggestion chips relevant to pinned context (viewing a patient → "Book follow-up", "Show last 3 visits", "Check balance")
- [ ] Composer context chips (attach a patient/appointment/invoice, max ~8)
- [ ] Settings toggle for clinic-level assistant enable/disable

## Data model

New: `ai_assistant_conversations`, `ai_assistant_messages`, `ai_assistant_actions`, `platform_settings` (or equivalent kill-switch storage). Extended: `clinics.ai_assistant_enabled`, `activity_log` (already supports `actor_type = 'ai_assistant'` since Phase 1).

## API endpoints

| Method     | Path                                            | Roles                                                                    |
| ---------- | ----------------------------------------------- | ------------------------------------------------------------------------ |
| POST (SSE) | `/api/v1/assistant/conversations/{id}/messages` | any authenticated clinic staff member, tool-level RBAC enforced per call |
| POST       | `/api/v1/assistant/actions/{id}/confirm`        | same as the underlying tool's RBAC                                       |
| POST       | `/api/v1/assistant/actions/{id}/cancel`         | same                                                                     |

## Edge cases & safety (do not skip any of these before calling a sub-phase done)

- A tool call with a forged/mismatched patient or appointment ID must fail exactly the way a direct API call with that ID would — the RBAC re-check has no special "AI path" leniency.
- An adversarial prompt attempt to get the assistant to bypass a Tier 2 confirm must be explicitly tested (per `mvp.md` §12: "Every Tier 2 action requires an explicit confirm click in a real test, including under a deliberately adversarial prompt attempt").
- Assistant failures (timeout, model error) must never leave a half-applied write — every write is queue-then-commit: the proposal is generated and stored, the actual DB write only happens on explicit confirm, and confirm itself is transactional.
- The kill switch (both platform and per-clinic) must be verified to instantly disable the assistant with no deploy needed — test this explicitly, not just document it.
- Bulk/cross-scope/external-send/clinical-write escalation rules must be tested with concrete adversarial-looking inputs (e.g. "cancel these 3 appointments" in one message; "book something for patient X" while viewing patient Y's page).
- The never-build list is enforced by _absence_ of a tool, not a prompt instruction — verify no tool exists for deleting a patient, deleting a chart version, or bulk-messaging.

## Testing

- pytest: full tier-classification matrix (base tier + every escalation rule, in combination), RBAC re-check on every Tier 0/1/2 tool, grounding-check strips an ungrounded claim in a mocked scenario, kill switch blocks requests immediately
- pytest: adversarial prompt suite — a set of deliberately manipulative user messages attempting to skip confirm, act cross-scope, or trigger a never-built tool; all must fail safely
- Vitest: chat panel rendering, confirm/cancel card interaction, streaming partial-render handling
- Playwright: end-to-end for at least one full flow per §9.7 ("Book Maria Santos for a follow-up next Tuesday afternoon", "What's Mr. dela Cruz's balance?", "Draft a SOAP note: ...")

## Docs to update in this phase

- `docs/architecture/ai-clinic-assistant.md` — this phase is where the doc stops being a spec and starts being a description of what's actually shipped; keep the tool catalog table current as each sub-phase lands
- `docs/mvp.md` §9.5 tool catalog table — confirm tier assignments match what shipped, update if a tool's real-world tier differs from the illustrative spec
- `mvp.md` §12 checklist — this phase satisfies the entire "AI assistant" checklist section

## Exit criteria

- [ ] Tier 0 tools shipped, safety-plumbed, and in real pilot use before Tier 1 work starts
- [ ] Tier 1 tools shipped and proven idempotent before Tier 2 work starts
- [ ] Every Tier 2 tool requires an explicit confirm, verified under adversarial testing
- [ ] Kill switch (platform + per-clinic) verified functional
- [ ] `activity_log` correctly attributes AI-executed actions with `actor_type = 'ai_assistant'`
- [ ] `pnpm run ci:quality` green, adversarial test suite green
