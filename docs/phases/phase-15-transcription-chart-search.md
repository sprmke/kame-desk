# Phase 15: Transcription + pgvector chart search

**Status:** Done
**Depends on:** Phase 14
**Unlocks:** Phase 16

**mvp.md reference:** §8.2 (ambient transcription half), §8.3

## Goal

A doctor can dictate during or after a consultation; the audio is transcribed on an ARQ worker (faster-whisper) and fed into Phase 14's SOAP-drafting pipeline. Separately, once a SOAP note is saved, an embedding is generated so doctors can search charts by meaning ("patients with recurring migraines in the last 6 months"), always linking back to the real chart version, never fabricating a result.

## Prerequisites

- Phase 14 done (SOAP drafting pipeline exists; transcription feeds into the same draft flow rather than being a separate feature)

## Tasks

### 1. Database

- [x] `soap_note_embeddings` table — soap_note_id, embedding (pgvector column), embedding_model_version, created_at
- [x] `consultation_recordings` table — appointment_id, r2_key (audio file), duration_seconds, transcription_status (`pending`/`processing`/`done`/`failed`), transcript_text (nullable until done), created_by_user_id, created_at

### 2. Backend

- [x] `POST /api/v1/appointments/{id}/recordings` — presigned R2 upload for the audio file, creates a `consultation_recordings` row, enqueues an ARQ job
- [x] ARQ job: `transcribe_recording` — runs faster-whisper on the VPS worker, writes `transcript_text`, updates status; on completion, optionally auto-triggers Phase 14's draft generation using the transcript as input (doctor still reviews/confirms exactly as before — transcription changes the _input_ to drafting, not the confirm requirement)
- [x] ARQ job: `generate_soap_embedding` — triggered on every SOAP note save (Phase 7's save service function enqueues this as a side effect, same "side effects live in the service function" rule as every other phase), embeds the note's clinical text, writes `soap_note_embeddings`
- [x] `GET /api/v1/clinics/{id}/chart-search?q=...` — semantic search: embeds the query, does a pgvector similarity search scoped to the clinic (and further scoped to the doctor's own patients unless the clinic's RBAC allows broader access, matching §6.11's clinical-notes row), returns results **linked to the real `soap_notes` row and version** — never a synthesized answer standing alone; the response is a ranked list of real chart references, not an LLM-generated summary of what might be there
- [x] Audio files: same presigned-URL-only access pattern as `patient_files` (Phase 3); short retention policy is a product decision to make explicit (recommend: keep raw audio only as long as needed to support transcription review/dispute, e.g. 90 days, then auto-delete via a scheduled ARQ job) — document the chosen retention window

### 3. Frontend

- [x] Recording control in the SOAP view — start/stop, upload progress, transcription status indicator, "use transcript to draft" button feeding into Phase 14's flow
- [x] `src/features/chart-search/` — semantic search bar (likely surfaced from a doctor's dashboard or patient list), results show snippet + patient name + visit date + link to the real chart version

## Data model

New: `soap_note_embeddings`, `consultation_recordings`.

## API endpoints

| Method | Path                                   | Roles                                                    |
| ------ | -------------------------------------- | -------------------------------------------------------- |
| POST   | `/api/v1/appointments/{id}/recordings` | doctor, owner                                            |
| GET    | `/api/v1/clinics/{id}/chart-search`    | doctor, owner (clinical-content RBAC, same as SOAP read) |

## Edge cases & safety

- Transcription is the single most PHI-dense audio data this product handles — encrypt at rest (R2 supports this; confirm bucket config), never transcribe/store audio for a clinic that hasn't consented per `mvp.md` §10's consent-capture requirement (verify consent exists before enabling recording for that clinic/patient).
- A failed transcription (worker crash, bad audio) must surface a clear retry path, not a silently stuck "processing" status forever — add a timeout that flips to `failed` after a reasonable window.
- Chart search must never let a doctor semantically discover another doctor's patient's clinical content if the clinic's RBAC scopes clinical notes to "own patients only" — the pgvector query's scope filter must mirror the exact same RBAC check as a direct SOAP read, not a looser one.
- Embedding generation failures (ARQ job error) must not block or roll back the SOAP save itself — the note is saved regardless; embedding is best-effort and retryable.
- Semantic search results are always a pointer to a real record, never a free-standing AI-generated summary of "what's probably in the chart" — this is explicit in `mvp.md` §8.3.

## Testing

- pytest: transcription job idempotency/retry, embedding generation triggered on save, chart search RBAC scoping matches SOAP-read RBAC exactly, audio retention job deletes on schedule
- Vitest: recording control states, search result rendering with a real chart-version link
- Manual QA: dictate a short note, confirm transcript quality is usable and the draft pipeline consumes it correctly

## Docs to update in this phase

- `docs/architecture/data-model.md` — pgvector usage, embedding model version tracking (so a future model upgrade can re-embed old notes without ambiguity)
- `docs/architecture/security-compliance.md` — audio retention policy, consent-gating for recording
- `docs/architecture/ai-clinic-assistant.md` — chart search grounding rule, referenced again when Phase 16's `search_charts` tool reuses this exact service function

## Exit criteria

- [x] Dictation → transcription → draft pipeline works end-to-end
- [x] Chart search returns real, correctly-scoped results with working links back to the source chart version
- [x] Consent is verified before recording is enabled for a clinic
- [x] `pnpm run ci:quality` green
