# Phase 7: SOAP versions, vitals, follow-up, specialty templates

**Status:** Done
**Depends on:** Phase 6
**Unlocks:** Phase 8

**mvp.md reference:** §6.5, §7.8, §7.9 · Gap closed: #8 and #9 in §7

## Goal

The clinical core of the product: SOAP consultation notes that are **never overwritten in place** (every save is a new version), specialty-specific templates (dental tooth chart, pediatric growth percentiles, etc.), and the follow-up date field that later phases (11, 12) actually act on.

## Prerequisites

- Phase 6 done: an appointment can reach `In Consultation` visit status, which is when a SOAP note is opened

## Tasks

### 1. Database

- [x] `soap_notes` table — append-only versions per appointment
- [x] `document_templates` table for SOAP-scoped templates
- [x] `clinics.reception_can_view_soap` for reception read opt-in
- [x] `visit_attachments` — reuse `patient_files` with `visit_id` (existing from Phase 3)

### 2. Backend

- [x] `POST /api/v1/appointments/{id}/soap-notes` — new version (doctor/owner write)
- [x] `GET /api/v1/appointments/{id}/soap-notes` — version history, `?version=N`
- [x] `POST /api/v1/appointments/{id}/soap-notes/{version}/sign`
- [x] `GET /api/v1/specialty-templates`
- [x] `GET /api/v1/appointments/{id}/soap-notes/{version}/pdf` — ReportLab renderer
- [x] RBAC: reception blocked by default; clinic opt-in via `reception_can_view_soap`

### 3. Frontend

- [x] `src/features/soap/` — SOAP form, template switcher, version history, PDF export
- [x] Vitals prefill from latest patient vitals
- [x] ICD-10 static typeahead
- [x] Follow-up date picker

## Exit criteria

- [x] SOAP notes are provably append-only (tested)
- [x] General, dental, pediatric specialty templates work
- [x] Reception default no-access verified (with clinic opt-in override test)
- [x] PDF export renders on letter size (skipped locally if `reportlab` not installed)
- [x] `pnpm run ci:quality` green
