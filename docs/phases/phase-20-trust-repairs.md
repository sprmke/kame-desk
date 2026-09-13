# Phase 20: Trust repairs

**Status:** Done
**Depends on:** Phase 19
**Unlocks:** Phase 21

**Plan reference:** `docs/workflow/planned/ground-up-app-redesign-and-platform-admin.md` §4 Phase 20 · **mvp.md** §8.1, §9, §8.8 (reminders)

## Goal

Nothing in the product should silently fail or claim to work when it does not. This phase wires the real LLM tool-calling loop both assistants were named for, sends SMS through Twilio (or fails visibly), refuses to pass off a canned visit summary as AI output, and blocks incomplete legally-facing documents the same way prescriptions already do.

## Prerequisites

- Phases 1–19 shipped (assistant tool registry, reminder rows, visit summaries, document issue path).
- `OPENAI_API_KEY` optional locally; production must set it for assistants and visit summaries to generate.

## Tasks

### 1. Backend

- [x] Shared PydanticAI OpenAI model factory (`app/ai/clients.py`) using `OpenAIChatModel` + `OpenAIProvider` (pydantic-ai 2.x). SOAP draft and safety-flag explain use the same factory so they no longer ImportError-fallback to stubs in production.
- [x] Staff assistant planner (`app/ai/assistant/planner.py`): structured `AssistantPlan` from PydanticAI. Execution still goes through `_execute_tool_calls` (RBAC, tiers, confirm). `__tool__:` remains a test/debug override for authenticated staff only.
- [x] Patient-facing assistant: production uses the same planner for write tools. Public `__tool__:` injection stays ignored unless `DOCTORDESK_TESTING=1`.
- [x] Real Twilio Messages API send in `app/services/sms_service.py`; reminder dispatch never writes `twilio-stub`. Failed sends mark `reminders.status=failed`.
- [x] Visit summary: `generation_failed` column. LLM/config failure stores an empty draft + flag, never a generic paragraph. Approve requires non-empty text.
- [x] `issue_document`: PRC license + signature completeness gate matching prescriptions (plus signature, required for certificates/referrals).

### 2. Frontend

- [x] `VisitSummaryPanel`: explicit "AI summary unavailable. Write it manually." when `generation_failed`. Send disabled until the doctor types a summary.

### 3. Testing

- [x] pytest: natural-language staff turn via mocked planner executes real tools
- [x] pytest: public `__tool__:` still ignored without `DOCTORDESK_TESTING`
- [x] pytest: public assistant LLM-planned booking executes when planner is mocked
- [x] pytest: visit summary generation failure is flagged and cannot be sent empty
- [x] pytest: document issue blocked without PRC/signature; succeeds when both present
- [x] pytest: SMS dispatch calls Twilio (httpx mocked); failures mark `failed`

## Data model

Extended: `visit_summaries.generation_failed` (boolean, default false). Migration `021_visit_summary_fail`.

## API endpoints

No new routes. `VisitSummaryRead` adds `generation_failed`.

## Edge cases & safety

- Model never executes tools itself. Planner returns names+args; the existing safety layer runs them.
- Public clients cannot inject `__tool__:` in production.
- SMS/visit-summary/LLM errors are logged with IDs only, never patient content.
- activity-log: N/A for planner (no new mutation). SMS send already logs via reminder dispatch cron. Document issue already logs. Visit summary generate already logs; metadata includes `generation_failed`.

## Docs to update in this phase

- `docs/architecture/ai-clinic-assistant.md` — real LLM planner, `__tool__:` is tests-only override
- `docs/architecture/data-model.md` — `generation_failed`
- `docs/architecture/deployment.md` — public `__tool__:` note
- `docs/guides/routes/dashboard/waiting-room.md` — visit summary failure UI
- `docs/guides/routes/dashboard/settings/notifications.md` — SMS actually sends
- `docs/guides/routes/dashboard/patients/documents.md` — PRC/signature gate
- `docs/phases/README.md` — Phase 20 row
- `docs/mvp.md` — assistant is LLM-driven in production

## Exit criteria

- [x] Assistants plan from natural language via PydanticAI when `OPENAI_API_KEY` is set (pytest covers the planner-to-tool path with a mocked model)
- [x] An SMS reminder either really sends via Twilio or is marked failed (never `twilio-stub`)
- [x] A failed AI visit summary is never mistaken for a real one
- [x] Certificates/referrals cannot issue without PRC license and signature
- [x] `pnpm run ci:quality` green
