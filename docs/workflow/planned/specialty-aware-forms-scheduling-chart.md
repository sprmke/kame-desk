---
title: Specialty-aware forms, public scheduling, and clinical chart
status: planned
updated: 2026-09-22
---

# Specialty-aware practice core

## Goal

Close the remaining gaps so DoctorDesk is a specialty-aware solo-clinic desk: the doctor’s specialty drives recommended clinical forms, patients can book from a public link without an account, and one Patient Record ties appointments, intake/forms, SOAP, and a chronological clinical timeline. **Reuse the shipped stack.** Do not rebuild onboarding, SOAP, patients, or public booking from scratch.

This plan is for **kame-desk** (FastAPI + TanStack Start). It is not work for kame-homes.

## Scope

### In

1. Typed doctor specialty on profile/onboarding, used to recommend forms.
2. Clinic-level enable/disable of specialty form templates (after product research).
3. Custom form builder (clinic-owned schemas, reusable across specialties).
4. Public booking intake + scheduling settings that the slot engine already almost supports.
5. Patient detail: Appointments tab, Forms tab, richer clinical timeline on Records.
6. SOAP stays appointment-linked, versioned, and signed; surface it in the chart.

### Out

- Multi-doctor booking UI, doctor-slug public URLs as the primary path, rooms, waitlist (`docs/mvp.md` §14). Keep `/book/:clinicSlug`.
- Replacing SOAP with generic forms. SOAP remains the encounter note.
- Mixing this with `document_templates` (certificates/referrals) or SOAP `specialty_data` JSON.
- Hard-coding one form pack for every specialty.
- Editing signed SOAP in place. Corrections stay new versions.
- Implementing inside **kame-homes**.

## Existing inventory (do not duplicate)

| Spec item                | Already shipped                                                                                            | Canonical paths                                                                  |
| ------------------------ | ---------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------- |
| Register                 | `/register`: name, clinic name, email, password                                                            | `apps/web/src/features/auth/pages/RegisterPage.tsx`, `apps/api/app/routers` auth |
| Onboarding               | Clinic → doctor → hours → fees → invite secretary                                                          | `apps/web/src/features/onboarding/`, `docs/guides/routes/onboarding.md`          |
| Doctor profile           | `doctor_profiles.specialty`, PRC, fees, `photo_url` column, signature upload                               | `apps/api/app/models/onboarding.py`, `.../settings/doctor/`                      |
| Specialty SOAP templates | general, dental, pediatric, obgyn, psychiatry, dermatology                                                 | `apps/api/app/data/specialty_templates.py`, SOAP page switcher                   |
| Dental odontogram        | Phase 39, dental template only                                                                             | `Odontogram.tsx`, `tooth_chart_entries`                                          |
| Public booking           | `/book/:slug`, no login, slots, find-or-create patient                                                     | `PublicBookingPage.tsx`, `public_booking.py`                                     |
| Hours / duration         | `clinics.working_hours`, holidays, `default_appointment_duration_minutes`, `service_fees.duration_minutes` | Hours settings, `slot_service.py`                                                |
| Patients                 | Search, list, create, merge, medical info                                                                  | `/dashboard/patients`                                                            |
| Patient detail tabs      | Overview, Records, Timeline, Rx, Billing, Documents, Activity                                              | `PatientDetailSubNav.tsx`                                                        |
| SOAP                     | S/O/A/P, versions, sign, PDF, AI draft, offline queue                                                      | `soap_service.py` (append-only), `/dashboard/appointments/:id/soap`              |
| Chart list               | Latest SOAP per visit on Records                                                                           | `GET /patients/{id}/charts`, `PatientChartList.tsx`                              |
| PHI on public            | Public API returns clinic/slots only; no SOAP                                                              | `PublicClinicRead`                                                               |

Relationship already in the DB:

```
users + clinic_memberships → clinics → doctor_profiles
patients (clinic_id) → appointments (patient, doctor, service_fee) → soap_notes (versioned)
patient_medical_info 1:1 patient
```

## Gap analysis

### 1. Doctor onboarding and signup

| Field                      | Today                                         | Change                                                                                        |
| -------------------------- | --------------------------------------------- | --------------------------------------------------------------------------------------------- |
| Full name, email, password | Register                                      | Keep                                                                                          |
| Clinic / practice name     | Register `clinic_name`                        | Keep                                                                                          |
| Clinic address             | Onboarding Clinic step                        | Keep                                                                                          |
| PRC                        | Onboarding Doctor step                        | Keep                                                                                          |
| Specialty                  | **Free-text** `<Input>`                       | Replace with catalog select + Other                                                           |
| Mobile                     | Clinic `contact_phone` only; no `users.phone` | Add optional `users.phone` (or reuse clinic phone for MVP) and collect on register/onboarding |
| Profile photo              | Column `photo_url`, **no upload UI**          | Mirror signature upload (presigned R2) on Doctor step + Settings → Doctor                     |
| Fees, hours, signature     | Shipped                                       | Keep                                                                                          |

Store specialty as a **stable key** (`dentist`, `obgyn`, …), not display copy. Map existing free-text rows in a one-shot data migration (`Family Medicine` → `general_practitioner`, unknown → `other` + `specialty_other` text).

Catalog (product, not UI copy dump): Dentist, OB-GYN, Pediatrician, General Practitioner, Dermatologist, Cardiologist, Ophthalmologist, Orthopedic, ENT, Other. Align keys with SOAP templates where they already exist (`dental`, `obgyn`, `pediatric`). Add SOAP templates later for cardiology / ophthalmology / orthopedic only when researched.

### 2. Specialty-based form selection

**Today:** SOAP template switcher is per visit. There is no clinic “form pack” (Patient Registration, Dental History, Consent, Periodontal Chart, …).

**Do not** overload `document_templates` or `specialty_data`. Those are letters and SOAP extras.

**New module:** clinical **form definitions** + **clinic enablement**.

```
specialty_key
  → platform form catalog (recommended defaults)
  → clinic_form_enablements (on/off, sort)
  → form_submissions (patient, optional appointment)
```

Dentists get a recommended pack (registration, dental history, medical history, exam, oral health, odontogram _already exists as tooth chart_, perio, treatment plan, dental SOAP _already exists_, consent, follow-up). Other specialties get their own catalog rows. Empty catalog is valid.

**Research gate (required before seeding non-dental packs):** product validates real forms per specialty. Until then, ship the **mechanism** + a **thin dental + general starter set**, and mark other specialties as “recommended list TBD”.

Doctors can enable, disable, preview schema, and manage later under Settings → Forms.

### 3. Custom form creation

Net-new. Reuse RHF + Zod + existing Field/Label primitives. Field types: short/long text, number, date, time, dropdown, single/multi choice, checkbox, yes/no, signature, file/image, measurement.

Builder capabilities: name, description, add/reorder fields, required, preview, edit, duplicate, archive (soft delete, never hard-delete submissions), save as clinic template.

Submissions are PHI: `clinic_id` from membership, RBAC same as SOAP read for clinical forms; reception can fill intake forms; public booking may only submit the **public intake** form, never SOAP.

### 4. Public patient scheduling

Keep **`/book/:clinicSlug`**. Solo MVP has one doctor; a doctor-slug alias can wait for Phase 2.

Extend the **existing** booker, do not add a second public app.

| Spec                | Today                                     | Change                                                                                                 |
| ------------------- | ----------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| Appointment type    | Services exist; public page ignores them  | Type picker → duration from `service_fees.duration_minutes`                                            |
| Date / time         | Shipped                                   | Keep `slot_service`                                                                                    |
| Patient info        | UI: name + phone. API also: email, reason | Surface email, DOB, sex, address, reason, new/existing, notes as **configurable** public-intake fields |
| Clinic hours / days | Shipped                                   | Keep                                                                                                   |
| Duration            | Clinic default                            | Per type                                                                                               |
| Breaks              | Open–close only                           | Optional `breaks: [{start, end}]` per day in `working_hours` JSON (additive, default none)             |
| Buffer              | None (slots abut)                         | `clinics.slot_buffer_minutes` (default 0)                                                              |
| Advance booking     | `min=today`                               | `clinics.advance_booking_days` cap                                                                     |
| Cancellation rules  | Reminders exist; no public policy         | Clinic setting + copy on confirm page only; no medical record on the public page                       |

Public response stays `PublicClinicRead` + slots. Never return SOAP, allergies, meds, or files.

### 5. Patient records

Keep the registry. Add:

- **Appointments** tab: `GET /appointments?patient_id=` (endpoint already lists clinic-wide; add/confirm patient filter). Do not invent a second calendar.
- **Forms** tab: submissions for that patient (Wave 4+).
- Overview already has personal info, allergies, conditions, meds, notes. Add emergency contact editor if the JSON field is display-only.

Do not rename Records to “Chart” in nav unless product wants it; map spec “Chart / Records” onto **Records**.

### 6. Chart / Records tab

`PatientChartList` is a title + date row. Upgrade to a **visit card** (staff SOAP read only):

- Date, visit/service label, doctor name
- Chief complaint (`reason_for_visit` / Subjective excerpt)
- Assessment / diagnosis
- Plan / treatment excerpt
- Link to full SOAP

Merge into the same chronological stream: visits (SOAP), completed forms, signed notes, tooth-chart planned/completed (dental), follow-up dates. Reception without `soap:read` sees visit dates only, not clinical text.

Do not dump invoices onto this clinical stream (those stay Timeline).

### 7. SOAP

Keep append-only versions. Map spec language:

| Spec                       | Existing                                   |
| -------------------------- | ------------------------------------------ |
| Draft                      | Latest unsigned version (`signed_at` null) |
| Finalized                  | `POST .../sign`                            |
| Do not overwrite finalized | No PATCH of clinical fields (already)      |

SOAP remains **appointment-scoped**. Walk-in already creates an appointment. Do not add orphan notes in MVP.

Show previous versions on the SOAP page (already) and excerpts on Records (Wave 3).

### 8. Data relationship (target)

```
Doctor (specialty_key)
  → Specialty form catalog (recommended)
  → Clinic enablements + custom forms
  → Public scheduling (clinic slug, hours, types)

Patient
  → Appointment (optional service_fee)
  → Form submissions (intake / visit)
  → SOAP versions (encounter)
  → Records timeline
```

All rows keep `clinic_id`. Public booking creates/finds `patients` then `appointments` with `booking_source=public_link` (already).

## Approach / trade-offs

1. **Wave 1–3 first** (refine existing). Wave 4–5 (forms) after the research gate and after design-overhaul screens for Patients/SOAP are stable (`docs/mvp.md` §13).
2. **Specialty key vs SOAP template key:** doctor specialty is a profile fact; SOAP template can default from it but the doctor may still switch per visit (locum content, mixed practice).
3. **Custom forms vs SOAP:** forms are questionnaires (intake, consent, history). SOAP is the clinician’s encounter documentation. A “Dental SOAP Note” recommended form should **deep-link to the SOAP editor**, not clone S/O/A/P in the form builder.
4. **Odontogram:** keep Phase 39 tooth chart; do not rebuild it as a form field. A “Tooth Chart” recommended form can be a pointer to that module.
5. **Working hours JSON:** extend in place (`breaks` optional). Do not migrate to a new table unless breaks become many-to-many later.
6. **Solo clinic:** one doctor calendar. Public page hides the doctor picker when `doctors.length === 1` (already).

## Implementation tasks

### Wave 1 — Specialty catalog, onboarding, photo

- [ ] Add `SPECIALTY_CATALOG` in API (`apps/api/app/data/specialties.py`) + web mirror. Keys + labels only.
- [ ] Alembic: `doctor_profiles.specialty_key` (nullable then backfill), `specialty_other` text; keep old `specialty` until backfill, then stop writing it.
- [ ] Alembic: `users.phone` optional.
- [ ] Register: optional mobile.
- [ ] `DoctorStep` + `DoctorProfilePage`: Select specialty (Other → text), PRC, photo dropzone (copy `signature-upload` → `photo-upload` in `doctors.py` / `storage_service.py`).
- [ ] SOAP page: default `specialty_template_key` from doctor `specialty_key` mapping (`dentist` → `dental`, unknown → `general`).
- [ ] Tests: onboarding, doctor PATCH, specialty list endpoint.
- [ ] Docs: `onboarding.md`, `settings/doctor.md`, `data-model.md`, `mvp.md` §6.1.

### Wave 2 — Public booking + scheduling settings

- [ ] Public UI: appointment type (from public clinic `services` once duration is in `PublicClinicRead`), then date, then slots with `duration_minutes`.
- [ ] Public UI: configurable intake (name/phone required; email, DOB, sex, address, reason, new/existing, notes). Persist on `patients` / `appointments.reason_for_visit` / `appointments.notes`.
- [ ] Clinic settings: buffer minutes, advance booking days, cancellation notice hours, `public_booking_auto_confirm` (already), public field toggles JSON.
- [ ] `working_hours` day object: optional `breaks[]`. `slot_service.get_available_slots` skips break windows and applies buffer between busy intervals.
- [ ] Confirm page: no PHI beyond the booking just made.
- [ ] Tests: `test_calendar_public_booking.py` (type duration, buffer, breaks, 409 still).
- [ ] Docs: `guides/routes/book.md`, clinic hours guide, `data-model.md`.

### Wave 3 — Patient Appointments tab + clinical timeline

- [ ] Confirm/filter `GET /appointments?patient_id=`.
- [ ] New tab **Appointments** on `PatientDetailSubNav` (keep Overview / Records / Timeline / …).
- [ ] Records: visit cards with S/O/A/P excerpts; `soap:read` gate unchanged.
- [ ] Empty/loading/error: existing `EmptyState` / skeletons.
- [ ] Docs: `patients/detail.md`.

### Wave 4 — Form catalog + enablement (after research)

- [ ] Product: validated field lists per specialty (start dental + general).
- [ ] Tables: `form_definitions` (platform or clinic owner, `schema_version`, JSON schema, `specialty_keys[]`, `kind`: intake / history / consent / exam / other), `clinic_form_enablements` (clinic_id, definition_id, enabled, sort), `form_submissions` (patient_id, appointment_id nullable, definition_id, answers JSONB, status draft/submitted, created_by).
- [ ] Settings → Forms: recommended vs other, enable/disable, preview.
- [ ] Patient Forms tab: fill/submit, list completed. Link submission to appointment when opened from a visit.
- [ ] Public: only definitions flagged `is_public_intake`.
- [ ] `activity_log` on enablement changes and submissions.
- [ ] RBAC: owner/admin/doctor manage definitions; reception fill intake; SOAP-equivalent read for clinical form answers.
- [ ] Docs: new route guide `dashboard/settings/forms.md`, `data-model.md`, `mvp.md` §6.x, `edge`/API conventions, plans N/A (solo clinic, not kame-homes entitlements).

### Wave 5 — Custom form builder

- [ ] Builder UI: field palette, reorder, required, preview, duplicate, archive.
- [ ] New clinic-owned `form_definitions` (`origin=clinic`).
- [ ] Signature + file fields: reuse presigned R2 patient files; store keys in answers, not bytes.
- [ ] Measurement: value + unit in schema.
- [ ] Tests: schema validation, archive hides from enablement but submissions remain.
- [ ] Docs: builder route guide.

## Docs to update (same change as code)

- `docs/mvp.md` §6.1, §6.3–6.5, public booking
- `docs/architecture/data-model.md` new tables / specialty_key
- `docs/guides/routes/onboarding.md`, `book.md`, `dashboard/settings/doctor.md`, `dashboard/settings/clinic.md`, `dashboard/patients/detail.md`, SOAP guide if default template changes
- `docs/guides/routes/README.md` for Settings → Forms
- `docs/phases/README.md` when this becomes an execution phase
- activity-log: emit on form/scheduling setting writes; N/A for catalog-only reads

## Open questions

1. **Research:** Who signs off dental vs OB vs pedia form packs before Wave 4 seed data?
2. **Mobile on user vs clinic:** Is doctor mobile a user field or only clinic `contact_phone`?
3. **Public `/book/{doctor-slug}`:** Defer to Phase 2 multi-doctor, or add a hidden alias now?
4. **Sequence vs design overhaul:** Waves 1–3 can land during Phases 44–47 if they reuse current components; Waves 4–5 should wait until Patients/SOAP screens are through the density pass.

activity-log: N/A — planning document only.
