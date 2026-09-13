# Phase 18: Patient-facing booking/FAQ assistant + AI visit summaries

**Status:** Done
**Depends on:** Phase 17
**Unlocks:** Phase 19

**mvp.md reference:** §8.4, §8.5 · Explicitly text-only for MVP — see §8.10, do not scope-creep into voice

## Goal

Two patient-facing (not staff-facing) AI additions: a text chat assistant embedded in the public booking page (Phase 4) that can check real availability and book, and answer clinic FAQs grounded only in that clinic's own settings data; and a short, editable, doctor-reviewable AI-generated visit summary sent to the patient after a visit completes.

## Prerequisites

- Phase 17 done. Phase 4's public booking page and Phase 16's assistant safety infrastructure (grounding checks, tier model concepts) both exist to be reused/adapted here — this is a **separate, more restricted assistant** from the staff-facing one in Phase 16, not an extension of it (per `mvp.md` §9.6: "hidden from patients — this is a staff/doctor tool ... the patient-facing assistant is the separate, more restricted §8.4 booking/FAQ assistant").

## Tasks

### 1. Patient-facing booking/FAQ assistant (§8.4)

- [ ] `app/ai/patient_assistant/` — a separate module from `app/ai/assistant/` (Phase 16), with its own, much smaller tool set: `check_public_availability` (reuses Phase 4's available-slots service function, same public-safe scoping — never exposes another patient's appointment details), `book_public_appointment` (reuses Phase 4's public booking endpoint's validation exactly), `answer_clinic_faq`
- [ ] **Grounding-facts builder** — a guest-safe context object built server-side containing _only_ clinic hours/services/booking-relevant settings data, never another patient's records, never internal fields — mirrors kame-homes' guest-safe grounding-facts pattern exactly
- [ ] **Independent safety check on output** — a second pass (separate from generation) that verifies the assistant's response doesn't claim clinic policy that isn't in the grounding facts and doesn't leak anything outside the guest-safe scope, before the response is shown — mirrors kame-homes' two-layer safety pattern for its own public-facing assistant
- [ ] Embed in Phase 4's public booking page as a chat widget alongside (not replacing) the existing slot picker
- [ ] No RBAC concept applies here (the caller is anonymous) — the entire safety model is the grounding-facts scoping + output safety check, since there's no user/role to check permissions against

### 2. AI visit summaries (§8.5)

- [ ] `generate_visit_summary` — PydanticAI call triggered when an appointment's visit status reaches `Completed` (Phase 5/6), taking the finalized SOAP note (Phase 7) and any issued prescriptions (Phase 8) as input, producing a short plain-language summary (what was discussed, prescriptions, follow-up date)
- [ ] Doctor reviews and can **edit or suppress** before it's sent — never auto-sent without this review step (reuses the reminder-sending infrastructure from Phase 11 for actual delivery once approved)
- [ ] `visit_summaries` table — appointment_id, generated_text, edited_text (nullable), status (`draft`/`approved`/`suppressed`/`sent`), reviewed_by_user_id, sent_at

### 2. Backend

- [ ] `POST /api/v1/public/clinics/{slug}/assistant/messages` (SSE) — patient-facing chat endpoint, anonymous, rate-limited same as Phase 4's other public endpoints
- [ ] `POST /api/v1/appointments/{id}/visit-summary/generate` — creates the draft
- [ ] `POST /api/v1/appointments/{id}/visit-summary/approve` — doctor approves (with edits accepted in the same call), triggers send via Phase 11's channel infrastructure
- [ ] `POST /api/v1/appointments/{id}/visit-summary/suppress` — doctor declines to send

### 3. Frontend

- [ ] Public booking page: chat widget, same mobile-first bar as the rest of the public page
- [ ] Visit summary review card on the visit-completion flow — short text, edit-in-place, Send/Suppress actions

## Data model

New: `visit_summaries`. No changes to the patient-facing assistant's data path beyond reusing `ai_assistant_conversations`-style logging scoped separately (or a distinct `patient_assistant_conversations` table if keeping the two systems fully separate is cleaner — recommended, to avoid any accidental cross-contamination between the staff and patient assistant data paths).

## API endpoints

| Method     | Path                                               | Auth                                  |
| ---------- | -------------------------------------------------- | ------------------------------------- |
| POST (SSE) | `/api/v1/public/clinics/{slug}/assistant/messages` | none (rate-limited, grounding-scoped) |
| POST       | `/api/v1/appointments/{id}/visit-summary/generate` | doctor, owner                         |
| POST       | `/api/v1/appointments/{id}/visit-summary/approve`  | doctor, owner                         |
| POST       | `/api/v1/appointments/{id}/visit-summary/suppress` | doctor, owner                         |

## Edge cases & safety

- The patient-facing assistant must never be able to answer a question by inventing clinic policy not present in the grounding facts ("do you accept my HMO?" must fail closed to "please contact the clinic" if that data isn't configured, never guess).
- The patient-facing assistant must never expose any other patient's booking, name, or reason for visit, even indirectly (e.g. "is 3pm free" must answer free/busy only, never "yes, after Maria's appointment").
- Visit summaries must never be sent without doctor approval — verify no scheduled job or automatic trigger sends one directly from `draft` status.
- A suppressed visit summary must be clearly distinguishable from a sent one in any audit trail, so a later "did the patient get a summary" question has an unambiguous answer.
- Rate-limit and monitor the public assistant endpoint for abuse (prompt injection attempts, scraping) — since it's unauthenticated, the same public-endpoint hardening from Phase 4 applies here too.

## Testing

- pytest: grounding-facts builder excludes all non-clinic-level data by construction (test with a fixture containing patient data mixed in, assert none of it can reach the builder's output), output safety check rejects a fabricated-policy response in a mocked scenario, visit summary never sends without approval
- Vitest: chat widget on public page, visit summary review/edit UI
- Playwright: patient books via the assistant on the public page end-to-end; doctor completes a visit, reviews and sends a summary

## Docs to update in this phase

- `docs/architecture/ai-clinic-assistant.md` — document the patient-facing assistant as an explicitly separate, more restricted system from Phase 16's staff assistant, with its own safety model
- `docs/guides/routes/book.md` — updated with the chat widget
- `mvp.md` §8.10 — confirm nothing in this phase accidentally reaches into voice/telemedicine scope explicitly deferred there

## Exit criteria

- [ ] Patient-facing assistant never leaks cross-patient data or invents clinic policy (tested)
- [ ] Visit summaries always require doctor approval before sending
- [ ] `pnpm run ci:quality` green
