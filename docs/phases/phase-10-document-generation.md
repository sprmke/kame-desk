# Phase 10: Document generation

**Status:** Done
**Depends on:** Phase 9
**Unlocks:** Phase 11

**mvp.md reference:** §6.8 · Gap closed: #12 in §7

## Goal

Clinics generate a steady stream of non-Rx paperwork (certificates, referrals, lab requests) from clinic-editable templates, auto-filled from patient/visit data, saved automatically to the patient's file attachments as an audit trail of what was issued.

## Prerequisites

- Phase 9 done (shares the PDF pipeline and letterhead/signature pattern established in Phases 7–9)

## Tasks

### 1. Database

- [ ] `document_templates` table (shared/extended from Phase 7's specialty-template table if that design was chosen — otherwise a new table with the same shape) — clinic_id (nullable = platform default template), type (`medical_certificate`/`referral_letter`/`lab_request`/`confinement_certificate`/`custom`), name, body_template (placeholder-based, e.g. Jinja2 or a simple `{{patient.full_name}}` token syntax), is_active
- [ ] `documents_generated` table — id, patient_id, appointment_id (nullable), template_id, type, final_content_snapshot (the actual rendered text/data at issue time — templates can change later, issued documents must not retroactively change), pdf_url, issued_by_user_id, issued_at

### 2. Backend

- [ ] `GET/POST/PATCH /api/v1/clinics/{id}/document-templates` — clinic-editable template CRUD (owner/admin only)
- [ ] `POST /api/v1/patients/{id}/documents` — render a document from a template + patient/visit context, returns a draft for review (never auto-issued)
- [ ] `POST /api/v1/documents/{id}/issue` — locks the `final_content_snapshot`, generates PDF, **auto-saves to `patient_files`** (per mvp.md §6.8: "All generated documents saved to the patient's file attachments automatically")
- [ ] `GET /api/v1/patients/{id}/documents` — history
- [ ] Placeholder resolution engine: a shared utility (used by this phase, referenced again by Phase 17's AI document generation tool) that safely fills `{{patient.full_name}}`, `{{clinic.name}}`, `{{doctor.signature_url}}` etc. — never allows an arbitrary/unescaped template to execute code (if using Jinja2, use a sandboxed environment, not the full Jinja2 `Environment`)

### 3. Frontend

- [ ] `src/features/documents/` — template library management (clinic settings), document generation flow from a patient/visit context (pick template → review filled-in draft → issue), document history on the patient page
- [ ] Print/PDF view

## Data model

New: `document_templates` (or extends Phase 7's), `documents_generated`.

## API endpoints

| Method         | Path                                      | Roles                                                                                                                                                                                                                |
| -------------- | ----------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| GET/POST/PATCH | `/api/v1/clinics/{id}/document-templates` | owner, admin                                                                                                                                                                                                         |
| POST           | `/api/v1/patients/{id}/documents`         | doctor, owner (documents like medical certificates are typically doctor-issued; confirm per-type if reception should draft non-clinical ones, e.g. a generic letterhead note — default to doctor/owner only for MVP) |
| POST           | `/api/v1/documents/{id}/issue`            | same                                                                                                                                                                                                                 |
| GET            | `/api/v1/patients/{id}/documents`         | owner, admin, doctor, reception (read)                                                                                                                                                                               |

## Edge cases & safety

- Template placeholder engine must be sandboxed — a clinic-editable template is user-controlled input from the platform's perspective; never allow template injection to reach arbitrary code execution or SSRF.
- A template edited after documents were already issued from it must not alter previously issued documents — `final_content_snapshot` is the permanent record, the template is just the generator.
- Auto-save to `patient_files` must tag the file with `file_type` appropriately so it's filterable alongside lab results/images (Phase 3).
- Certificates/referrals are clinical-adjacent documents — apply the same doctor/owner-only issuance default as prescriptions unless a clinic explicitly needs otherwise.

## Testing

- pytest: template rendering with missing/optional placeholders handled gracefully, snapshot immutability after template edit, sandboxed rendering rejects an injection attempt
- Vitest: template editor, document review-before-issue flow
- Playwright: generate a certificate end-to-end, confirm it appears in patient files

## Docs to update in this phase

- `docs/architecture/data-model.md`
- `docs/guides/routes/dashboard/patients/documents.md` and `dashboard/settings/document-templates.md`

## Exit criteria

- [x] Clinic can create/edit at least one template per document type
- [x] Generated documents auto-save to patient files and are immutable after issue
- [x] Placeholder engine is sandboxed against injection
- [x] `pnpm run ci:quality` green (API pytest + web vitest/build)
