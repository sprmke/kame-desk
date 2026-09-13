# SOAP note (`/dashboard/appointments/:appointmentId/soap`)

**Status:** Documented

## Behavior

- S/O/A/P form with specialty template switcher (general, dental, pediatric, OB-GYN, psychiatry, dermatology). Dental renders a real interactive odontogram (Phase 39, below); pediatric has height/weight/percentile; OB has gravida/para/LMP/EDD; psychiatry has MSE/risk; dermatology has location/morphology. Loading uses a form skeleton; SOAP fields use shared placeholders. Versions, diff, and the clinician note are unboxed sections. The AI draft block uses a dashed border so it reads as draft, not as signed chart.
- Each **Save** creates a new version (append-only). Version history is read-only. **Diff** compares two versions field by field.
- **Sign latest** applies the doctor signature from profile settings.
- **PDF** opens a rendered note (letter size).
- Vitals: latest patient vitals prefill the Objective field on a new version.
- **AI draft (Phase 14):** short free-text input streams S/O/A/P into the form over SSE. Nothing saves until **Save**.
- **Recording (Phase 15):** record consultation audio, transcribe on worker, **Use transcript** feeds the AI draft flow. Requires clinic recording consent in settings.
- ICD-10 typeahead from a static catalog.
- Follow-up date is optional (calendar picker); Phase 11 recalls read this field.
- **Offline (Phase 36):** if the connection drops mid-visit, **Save** queues the note locally (IndexedDB) instead of failing. The page shows "Saved locally. Will sync when you are back online." The queued draft syncs automatically on reconnect, tagged with a `client_draft_token` so a retried flush can't create a duplicate version. This is the only write path in the product that works offline; see `docs/architecture/offline-resilience.md`.
- **Odontogram (Phase 39, dental template only):** a 32-tooth adult (FDI numbering) interactive chart, upper/lower arches. Tapping a tooth opens a picker (surface — or "whole tooth" — condition, and status: existing/planned). Findings save immediately to the patient's tooth chart (independent of SOAP versioning — a running per-patient chart, not a per-visit snapshot) and color-code the tooth by its latest condition. A tooth marked `missing` disables surface-level charting on it (only whole-tooth entries). **History** toggles a full chronological list across all teeth and visits; findings are append-only — a new visit's finding never overwrites a prior one, so progression (e.g. caries → filled → crown) stays visible. A **Treatment plan** section lists all `planned` entries clinic-wide for the patient with an **Add to invoice** action per entry, which creates (or appends to) a draft invoice for the visit and marks the entry `completed`. An empty chart sits in a card.

## Save paths

| Action                     | API                                                                | DB effect                                                                     |
| -------------------------- | ------------------------------------------------------------------ | ----------------------------------------------------------------------------- |
| Save version               | `POST /api/v1/appointments/{id}/soap-notes`                        | new `soap_notes` row, `activity_log`                                          |
| AI draft                   | `POST /api/v1/appointments/{id}/soap-draft` (SSE)                  | no DB write; increments `clinic_ai_usage`                                     |
| Recording                  | `POST /api/v1/appointments/{id}/recordings` + `/submit`            | `consultation_recordings`; ARQ transcribe                                     |
| List versions              | `GET /api/v1/appointments/{id}/soap-notes`                         | read                                                                          |
| Sign                       | `POST /api/v1/appointments/{id}/soap-notes/{version}/sign`         | `signed_at`, `activity_log`                                                   |
| PDF                        | `GET /api/v1/appointments/{id}/soap-notes/{version}/pdf`           | read                                                                          |
| Templates                  | `GET /api/v1/specialty-templates`                                  | static catalog                                                                |
| Tooth chart list           | `GET /api/v1/patients/{id}/tooth-chart`                            | read                                                                          |
| Tooth chart entry          | `POST /api/v1/patients/{id}/tooth-chart`                           | new `tooth_chart_entries` row, `activity_log`                                 |
| Add tooth entry to invoice | `POST /api/v1/patients/{id}/tooth-chart/{entry_id}/add-to-invoice` | `invoice_line_items` row (new or appended draft invoice); entry → `completed` |

## Validation

- Write: `doctor` or `owner` only; doctor must match appointment `doctor_id` unless owner.
- Read: `owner`, `admin`, `doctor`; `reception` only when `clinics.reception_can_view_soap` is true.

## RBAC

| Role      | Read          | Write                  |
| --------- | ------------- | ---------------------- |
| owner     | yes           | yes                    |
| admin     | yes           | no                     |
| doctor    | yes           | yes (own appointments) |
| reception | clinic opt-in | no                     |

Tooth chart read uses the same `assert_soap_read` gate as SOAP notes. Tooth chart write uses `assert_clinical_notes_write` (owner or doctor role) — unlike SOAP write, it does not additionally check the entry's appointment is the writing doctor's own, since a patient's tooth chart is shared clinic-wide clinical state, not a single doctor's per-visit note.

## AI assistant parity

Phase 14 SOAP draft is a direct UI feature. `draft_soap_note` assistant tool ships in Phase 16.

## Edge cases

- AI draft is pre-save form state only. Dropped SSE leaves partial fields editable.
- Daily AI cap (`AI_DAILY_REQUEST_CAP`, default 100) returns 429; manual SOAP entry still works.

- No PATCH/PUT route for clinical content; corrections are new versions.
- PDF renders a blank signature line when no signature image is uploaded.
- `specialty_data` JSON includes `schema_version` for forward-compatible templates.
- Two tabs/devices saving the same offline draft: last-write-wins with a visible version/timestamp, same as any two online saves — true multi-device conflict resolution is out of scope for MVP.
- A queued offline draft whose appointment was deleted in the meantime: the flush drops that entry (its `client_draft_token` never matches a valid appointment) rather than blocking every draft queued after it.
- Same tooth charted across multiple visits (progression caries → filled → crown): history is additive, never overwrites a prior entry; the odontogram's tooth color reflects the entry with the latest `noted_at` for that tooth.
- A tooth marked `missing`: the surface picker is disabled for that tooth (a missing tooth has no surfaces to chart); only whole-tooth entries remain possible.
- Adding a planned tooth entry to invoice reuses an existing draft invoice for the same appointment if one exists, otherwise creates a new draft invoice — it never creates a second draft for the same visit. When no appointment context is known at all, it always creates a new draft rather than risking a match against an unrelated older draft for the same patient.
- A `completed` tooth entry cannot be added to an invoice again (400) — its `invoice_line_item_id` already points at the line that was created.
- Deleting the invoice line item a tooth entry was billed under reverts that entry back to `planned` (its `invoice_line_item_id` is cleared) so the procedure reappears on the treatment plan and can be re-billed.

## Implementation map

- Web: `features/soap/pages/SoapNotePage.tsx`, `hooks/useSoapDraftStream.ts`, `SpecialtyFields.tsx`, `components/Odontogram.tsx`, `lib/offlineSoapQueue.ts`, `lib/offlineSoapSync.ts`
- API: `routers/soap.py`, `services/soap_service.py`, `app/ai/soap_draft_service.py`, `services/ai_usage_service.py`, `routers/tooth_chart.py`, `services/tooth_chart_service.py`
- Migration: `034_soap_client_draft_token.py`, `039_tooth_chart.py`

## Host-facing knowledge

Open **SOAP** from the appointments list during or after a visit. Every save keeps prior versions. Sign when the note is final. Reception cannot see notes unless the clinic enables it in settings. If the connection drops while writing a note, keep working — Save still works and shows "Saved locally"; it syncs to the server automatically once the connection is back, no need to re-save. For dental patients, switch the template to Dental to chart teeth visually — tap a tooth, pick a surface (or the whole tooth) and a condition, and it saves right away as part of that patient's ongoing dental history, not tied to a single visit note. Mark a finding "Planned" to add it to the treatment plan, then push it straight to an invoice from there once the patient agrees to the procedure.
