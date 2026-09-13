# AI Clinic Assistant — architecture

This is the living implementation reference for the flagship feature specified in full in `docs/mvp.md` §9. That section is the authoritative spec; this doc tracks what's actually shipped, tool by tool, and records the concrete engineering patterns (prompt context, grounding rules) other AI phases reuse. Update this doc's tool catalog table every time Phase 14–18 work lands or changes.

**Phase 14 shipped:** SOAP draft SSE (`POST /api/v1/appointments/{id}/soap-draft`) via `app/ai/` with per-clinic daily cap in `clinic_ai_usage`. Local/tests use a stub provider when `DOCTORDESK_TESTING=1` or `OPENAI_API_KEY` is unset; production uses PydanticAI + `gpt-4o-mini` when configured.

**Phase 16 shipped:** Staff AI Clinic Assistant under `app/ai/assistant/` with SSE chat (`POST /api/v1/assistant/conversations/{id}/messages`), Tier 0–2 tool registry, confirm/cancel for Tier 2 (`POST /api/v1/assistant/actions/{id}/confirm|cancel`), platform kill switch (`PLATFORM_AI_ASSISTANT_ENABLED`, default off) plus per-clinic `clinics.ai_assistant_enabled`.

**Phase 20 shipped:** Production turns use a PydanticAI structured planner (`app/ai/assistant/planner.py`) that returns tool names+args. Tools still execute only through the existing RBAC/tier/confirm layer. `__tool__:{json}` remains a test/debug override for authenticated staff. Public/guest clients cannot inject `__tool__:` unless `DOCTORDESK_TESTING=1`. SOAP draft and safety-flag explain share `app/ai/clients.py` (`OpenAIChatModel` + `OpenAIProvider`). Visit summaries set `generation_failed` instead of substituting a canned paragraph. SMS reminders call Twilio. Certificates/referrals require PRC license and signature on issue.

**Phase 29 shipped:** Confirm cards show the proposal payload. The web composer sends `page_context` from the current route. Book/reschedule outside 08:00–18:00 or with `overlap_risk` escalate to Tier 2. Owners can disable tools (`clinics.assistant_disabled_tools`) and read `GET /assistant/usage`. The chat UI renders patient/appointment/invoice result cards and suggested prompts.

**Phase 30 shipped:** Platform flag `ai_assistant` overrides the env kill switch when a `platform_feature_flags` row exists.

**Read before touching any AI code:** `mvp.md` §8–§9 in full, `.cursor/rules/ai-assistant-safety.mdc` (created in Phase 0).

## Two separate assistants — do not conflate them

|                       | Staff-facing (AI Clinic Assistant)                      | Patient-facing (booking/FAQ assistant)                                                                         |
| --------------------- | ------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| Phase                 | 16                                                      | 18                                                                                                             |
| Audience              | Clinic staff/doctors, authenticated                     | Anonymous patients on the public booking page                                                                  |
| Module                | `apps/api/app/ai/assistant/`                            | `apps/api/app/ai/patient_assistant/`                                                                           |
| Safety model          | RBAC re-check + 3-tier risk model                       | Grounding-facts scoping + independent output safety check (no RBAC — caller is anonymous)                      |
| Can write clinic data | Yes, tiered (Tier 1 auto, Tier 2 confirm)               | Yes, but only `book_public_appointment` — the exact same validated path Phase 4's public booking endpoint uses |
| Visibility            | Floating launcher, dashboard only, hidden from patients | Embedded in the public booking page only                                                                       |

## Context model (staff assistant, Phase 16)

| Signal              | Meaning                                                             | Source         |
| ------------------- | ------------------------------------------------------------------- | -------------- |
| `pageContext`       | The screen the user is on (`patientId`, `appointmentId`, `visitId`) | Current route  |
| `attachedContext[]` | Explicit items pinned in the composer, max ~8                       | Composer chips |

**Argument resolution order:** explicit args in the user's message → attached context → ambient page context. This is what prevents the assistant from acting on the wrong patient when a user has multiple charts open across tabs. Implemented in `app/ai/assistant/context.py` (Phase 16).

## Three-tier risk model (server-computed, never model-decided)

| Tier                 | Meaning                                                                             | Examples                                                                                                                                                              |
| -------------------- | ----------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 0 — read             | Always allowed if RBAC passes, never writes                                         | `search_patients`, `get_patient`, `list_appointments`, `get_available_slots`, `check_patient_balance`, `search_charts`, `draft_soap_note`, `check_eligibility_status` |
| 1 — auto-executed    | Idempotent, low blast radius, runs automatically, surfaced as a visible "done" card | Revoke a not-yet-accepted staff invite, simple forward-only appointment status move                                                                                   |
| 2 — confirm required | Tool returns a proposal; nothing writes until the user taps Confirm                 | Cancel appointment, issue prescription, create invoice line, send reminder, edit clinical notes, change clinic settings                                               |

**Escalation rules (always override a tool's default tier):**

1. **Bulk** — 2+ writes requested in one turn → every one becomes Tier 2
2. **Cross-scope** — acting outside current page context and outside pinned context → Tier 2
3. **External-send** — anything that sends a real message to a patient → always Tier 2, distinct destructive-styled confirm ("Send", not generic "Confirm")
4. **Clinical-write** — any SOAP/prescription/diagnosis write → always Tier 2, no exceptions

## Safety model (every tool, no exceptions)

1. Independent RBAC re-check per tool call, re-derived from the original request's auth token — never trusts anything the model asserts about caller identity or permissions.
2. Pre-execution re-check against current DB state immediately before writing, even for Tier 1 — mismatches hard-fail instead of writing over stale assumptions.
3. Post-generation grounding check — every stated fact (balance, date, status) verified against real tool-result data before display; ungrounded claims are stripped, never shown.
4. Full audit trail — every executed write recorded to `activity_log` with `actor_type = 'ai_assistant'`, visible on the relevant record as "Actions taken by AI assistant."
5. Never-build list enforced by tool _absence_ — irreversible/maximal-blast-radius actions (delete a patient, delete a chart version, bulk-message all patients) are never registered as callable tools.
6. Per-clinic daily AI usage cap, enforced server-side before any model call (shared with Phase 14's SOAP drafting cap).

## Prompt context minimization (applies to every AI feature, not just the assistant)

The minimum necessary data for the specific call, never the patient's entire history by default:

| Feature                             | What's sent to the model                                                                                                      |
| ----------------------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| SOAP draft (Phase 14)               | Current visit's short input + current visit's vitals/chronic conditions only                                                  |
| Chart search (Phase 15)             | The search query only; results are real DB rows returned post-search, not generated by the model                              |
| Assistant tool calls (Phase 16)     | Tool-specific arguments + the minimum record data that tool's schema requires                                                 |
| Patient-facing assistant (Phase 18) | Grounding-facts object only (clinic hours/services/booking data) — **never** another patient's records, never internal fields |

Never log raw prompts/responses containing patient content to general application logs or Sentry. AI-call logging (tool name, tier, outcome) is structured and kept separate from the clinical `activity_log`, per `mvp.md` §10 Observability.

## Grounding-facts pattern (patient-facing assistant, Phase 18)

A guest-safe context object built server-side, containing only clinic-level, booking-relevant data (hours, services, accepted HMOs if configured) — never another patient's records, never internal system fields. An independent, separate pass checks the assistant's generated output against these facts before it's shown, rejecting any claim not grounded in them. This mirrors kame-homes' two-layer safety pattern for its own public-facing guest assistant, applied to DoctorDesk's smaller, text-only, clinic-FAQ scope.

## Tool catalog (updated as Phase 16/17/18 ship — status column is the source of truth)

| Tool                                                                      | Type                                                             | Tier                                                   | Phase | Status  |
| ------------------------------------------------------------------------- | ---------------------------------------------------------------- | ------------------------------------------------------ | ----- | ------- |
| `search_patients`                                                         | read                                                             | 0                                                      | 16    | Shipped |
| `get_patient`                                                             | read                                                             | 0                                                      | 16    | Shipped |
| `list_appointments`                                                       | read                                                             | 0                                                      | 16    | Shipped |
| `get_available_slots`                                                     | read                                                             | 0                                                      | 16    | Shipped |
| `check_patient_balance`                                                   | read                                                             | 0                                                      | 16    | Shipped |
| `search_charts`                                                           | read                                                             | 0                                                      | 16    | Shipped |
| `draft_soap_note`                                                         | read                                                             | 0                                                      | 16    | Shipped |
| `revoke_pending_staff_invite`                                             | write                                                            | 1                                                      | 16    | Shipped |
| `advance_appointment_status` (forward-only, no financial/clinical impact) | write                                                            | 1                                                      | 16    | Shipped |
| `propose_book_appointment`                                                | write                                                            | 1 (routine) / 2 (outside hours or double-booking risk) | 16    | Shipped |
| `propose_reschedule_appointment`                                          | write                                                            | 1 (simple move) / 2 (same-day/short-notice)            | 16    | Shipped |
| `propose_cancel_appointment`                                              | write                                                            | 2 (always)                                             | 16    | Shipped |
| `propose_save_soap_note`                                                  | write                                                            | 2 (always)                                             | 16    | Shipped |
| `propose_issue_prescription`                                              | write                                                            | 2 (always)                                             | 16    | Shipped |
| `propose_create_invoice_line`                                             | write                                                            | 2 (always)                                             | 16    | Shipped |
| `propose_send_reminder`                                                   | write                                                            | 2 (always) + external-send styling                     | 16    | Shipped |
| `propose_generate_document`                                               | write                                                            | 2 (always)                                             | 16    | Shipped |
| `explain_safety_flag`                                                     | read (explanatory only, never decides)                           | 0 (standalone REST, not chat tool)                     | 17    | Shipped |
| `extract_billing_document`                                                | read (produces an editable draft, never writes)                  | 0 (standalone REST, not chat tool)                     | 17    | Shipped |
| `check_public_availability`                                               | read (public assistant)                                          | n/a (no RBAC — anonymous)                              | 18    | Shipped |
| `book_public_appointment`                                                 | write (public assistant)                                         | n/a                                                    | 18    | Shipped |
| `answer_clinic_faq`                                                       | read (public assistant)                                          | n/a                                                    | 18    | Shipped |
| `generate_visit_summary`                                                  | read (produces a draft, never sends)                             | n/a                                                    | 18    | Shipped |
| `check_eligibility_status`                                                | read (latest on-file HMO/PhilHealth check, no live insurer call) | 0                                                      | 33    | Shipped |

**Never-build list (explicitly never registered as a tool, for either assistant):** delete a patient record, delete a chart version, bulk-message the entire patient list, any direct SQL/raw-query execution tool, any tool that changes another clinic's data, any tool that disables RBAC/audit logging.

## UI/UX reference

- Floating launcher, bottom-right, every dashboard screen, hidden from patients (staff assistant only)
- Chat panel: streaming text, structured cards (patient/appointment/invoice — a `ChatBlock`-equivalent component set), confirm/cancel cards for Tier 2
- Quick-action suggestion chips relevant to pinned context
- SSE streaming (see `docs/architecture/api-conventions.md` § Streaming)
- Two-layer kill switch: platform-wide default-off flag + per-clinic Settings toggle, both checked before any request is served

## Related docs

- `docs/mvp.md` §8–§9 — full product spec (authoritative)
- `docs/phases/phase-14-ai-soap-draft-sse.md` through `phase-18-patient-facing-assistant.md` — build sequence
- `.cursor/rules/ai-assistant-safety.mdc` — the always-on rule version of this doc's safety model, read by every agent session
