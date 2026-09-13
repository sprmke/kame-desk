# Phase 14: PydanticAI SOAP draft + SSE streaming

**Status:** Done
**Depends on:** Phase 13
**Unlocks:** Phase 15

**mvp.md reference:** §8.2 (draft/expand behavior only — transcription is Phase 15) · Read `docs/architecture/ai-clinic-assistant.md` before starting (shared safety patterns apply even though the assistant itself is Phase 16)

## Goal

The first AI feature in the product: a doctor types a short note ("BP high, refill maintenance meds, follow up 2 weeks") and PydanticAI expands it into a structured SOAP draft that **streams into the form field-by-field** over SSE, visible as it generates. The doctor always reviews and explicitly confirms before anything is saved as a real chart version (Phase 7's versioning rule is absolute — this phase cannot weaken it).

## Prerequisites

- Phase 13 done (SOAP notes, versioning, and the audit log are all solid before AI writes anything near them)
- OpenAI/Gemini API keys provisioned; per-clinic daily AI usage cap design decided (see Edge cases)

## Tasks

### 1. Backend

- [x] `app/ai/` module structure: `clients.py` (LLM client wiring), `prompts/soap_draft.py`, `schemas.py` (PydanticAI output models mirroring `soap_notes` fields: subjective/objective/assessment/plan/diagnosis suggestions/follow-up suggestion)
- [x] PydanticAI agent: takes a short free-text input + optional pulled context (patient's latest vitals, existing chronic conditions from Phase 3) and produces a structured `SoapDraft` Pydantic model — **never writes directly to `soap_notes`**, this is generation only
- [x] `POST /api/v1/appointments/{id}/soap-draft` (SSE response) — streams the draft generation token-by-token/field-by-field to the client; the endpoint itself does not persist anything
- [x] Per-clinic daily AI usage cap: a `clinic_ai_usage` table (clinic_id, date, request_count, token_count or cost_estimate) incremented on every AI call, checked _before_ calling the model — enforced server-side, not just measured after the fact (per mvp.md §9.4 point 6, applied here even though this predates the full assistant)
- [x] Model routing: cheap model (GPT-4o-mini / Gemini Flash) by default per `tech-stack.md`; do not add a "stronger model" escalation path in this phase unless a pilot doctor explicitly requests it — keep cost-aware defaults as shipped

### 2. Frontend

- [x] SOAP form (Phase 7) gets an "AI draft" entry point: short free-text input → SSE stream renders into S/O/A/P fields live, each field visibly editable the moment it's populated (not a locked preview) — the doctor is drafting _with_ the assistant, not receiving a black box
- [x] Explicit "This is an AI draft — review before saving" indicator persists until the doctor's first manual edit or explicit acceptance
- [x] The existing Phase 7 save flow is completely unchanged — saving still creates a new immutable version exactly as before; the AI draft only ever populates the _pre-save_ form state

## Data model

New: `clinic_ai_usage` (usage caps). No changes to `soap_notes` — the AI draft never touches persisted clinical data before a human save.

## API endpoints

| Method     | Path                                   | Roles                                                         |
| ---------- | -------------------------------------- | ------------------------------------------------------------- |
| POST (SSE) | `/api/v1/appointments/{id}/soap-draft` | doctor, owner (same doctor-only gate as SOAP writes, Phase 7) |

## Edge cases & safety

- **The AI must never write a chart version directly** — verify with a test that the draft endpoint has no code path that calls the Phase 7 save service function.
- A dropped SSE connection mid-stream must leave the form in a clean partial state (whatever streamed in stays, editable) — never a stuck spinner or a corrupted field.
- The daily usage cap, once hit, must fail the request with a clear "AI drafting unavailable today" message and a working manual-entry fallback — the manual SOAP form from Phase 7 must remain fully usable with the AI feature entirely disabled (mirrors mvp.md §10: "AI assistant failures must never block the underlying manual workflow").
- Patient data sent to the LLM must be the minimum necessary (current visit context only, not the patient's entire history) per PHI-minimization — document exactly what's included in the prompt in `docs/architecture/ai-clinic-assistant.md`.
- Never log the raw prompt/response containing patient content to general application logs; if AI-call logging is needed for debugging, log tool/call metadata only (per `mvp.md` §10 Observability: "Structured logs for every AI tool call ... separate from the clinical audit log, for debugging without exposing patient content").

## Testing

- pytest: draft generation produces valid structured output against a fixture input, usage cap enforcement blocks the call once exceeded, no code path persists a draft without an explicit save call
- Vitest: SSE stream rendering into form fields, partial-stream-then-drop handling
- Manual QA: verify a doctor can ignore the AI entirely and use the plain Phase 7 form with zero degradation

## Docs to update in this phase

- `docs/architecture/ai-clinic-assistant.md` — first real AI feature; document the prompt-context-minimization rule concretely here since Phase 16 reuses this pattern
- `docs/mvp.md` §15 open question #4 (AI cost ownership) — flag if still unresolved before enabling this in front of a real pilot clinic

## Exit criteria

- [x] AI draft streams visibly into the SOAP form and never auto-saves
- [x] Daily usage cap enforced and tested
- [x] Manual SOAP entry (Phase 7) works identically with AI drafting disabled
- [x] `pnpm run ci:quality` green
