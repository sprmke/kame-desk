# KameDesk — MVP Product Requirements Document

**Product:** DoctorDesk
**Tagline:** _Your Clinic. Simplified._
**Version:** 1.2 (solo-clinic MVP)
**Status:** Active — supersedes v1.1 multi-doctor / multi-clinic expansion
**Last updated:** 2026-09-16

Related docs: [`tech-stack.md`](./tech-stack.md) (how to build), [`README.md`](./README.md) (index).

> This document is the single source of truth for **what clinic staff see in the DoctorDesk MVP**. APIs, tables, and tests for deferred modules stay in the repo. Do not delete them. Do not surface them in nav, onboarding, or marketing copy.

---

## Table of contents

1. [Executive Summary](#1-executive-summary)
2. [Problem Statement](#2-problem-statement)
3. [Target Users](#3-target-users)
4. [Product Goals & Success Metrics](#4-product-goals--success-metrics)
5. [Scope Overview](#5-scope-overview)
6. [Core Modules (MVP)](#6-core-modules-mvp)
7. [Why these stay](#7-why-these-stay)
8. [Modern & AI Features](#8-modern--ai-features)
9. [AI Clinic Assistant](#9-ai-clinic-assistant)
10. [Non-Functional Requirements](#10-non-functional-requirements)
11. [Data Model](#11-data-model)
12. [Production Readiness Checklist](#12-production-readiness-checklist)
13. [Build Order / Remaining work](#13-build-order--remaining-work)
14. [Out of Scope for MVP (Phase 2+)](#14-out-of-scope-for-mvp-phase-2)
15. [Open Questions](#15-open-questions)

---

## 1. Executive Summary

DoctorDesk is clinic desk software for **one doctor and one secretary**. It replaces paper SOAP notes, the appointment book, handwritten prescriptions, and visit/procedure/medicine money tracking (including HMO paperwork). An **AI Clinic Assistant** sits on top so the same jobs can be done by chat, not only by clicking screens.

The MVP bar: **that pair can go live without a parallel paper or spreadsheet system.** No second doctor, second branch, or patient app is required.

**Daily loop**

1. Secretary books or takes a walk-in.
2. Patient waits; secretary moves Arrived → In consult → Done.
3. Doctor writes SOAP (or asks the assistant to draft) and issues a prescription.
4. Secretary records the invoice (self-pay or HMO) and prints what the patient needs.

---

## 2. Problem Statement

Independent clinics in the Philippines (dentist, pedia, OB-GYN, family/internal med, ENT) still run on paper charts, a notebook calendar, handwritten Rx, and a cash notebook. That causes lost notes, double-booked slots, slow consults, and no clear picture of what was charged or collected.

DoctorDesk is the one desk for that clinic. It is not a hospital EMR, not a lab LIS, and not a multi-branch franchise system.

---

## 3. Target Users

**Primary:** one practicing doctor (dentist, pediatrician, OB-GYN, family medicine, internal medicine, ENT, or similar outpatient specialty).

**Secondary:** one secretary / receptionist who runs the calendar, waiting room, billing, and HMO papers.

**Persona (the only MVP persona)**

| Persona                | Context                                                                                     | What they need                                                                                                           |
| ---------------------- | ------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| **Doctor + secretary** | One clinic, one doctor calendar. The doctor may also run the desk if there is no staff yet. | Fast SOAP and Rx for the doctor. Booking, queue, invoices, and HMO for the secretary. Chat assistant as a parallel path. |

**Not this MVP:** 2–5 doctors sharing a front desk, locum calendars, rooms, or multi-clinic organizations. Those are **Phase 2**. The data model still has `clinic_id` and `doctor_id`. Clinic UI assumes one doctor.

**Roles in the UI**

| Role          | Who                      | SOAP                                      | Calendar / billing |
| ------------- | ------------------------ | ----------------------------------------- | ------------------ |
| **Owner**     | The doctor who signed up | Full                                      | Full               |
| **Reception** | Secretary                | No access unless the clinic turns on view | Full               |

`admin` and extra `doctor` remain in the API. Onboarding and Team invite only offer **secretary** (`reception`). Reception cannot edit SOAP.

---

## 4. Product Goals & Success Metrics

### Goals

- Replace paper SOAP, the appointment book, paper Rx, and visit money tracking
- Keep the desk simple enough that two people can learn it in a morning
- Cut no-shows with email confirm + 24h reminder
- Let the assistant book, look up a patient, draft SOAP, and help with billing/HMO

### Success metrics (pilot)

| Metric                                                         | Target                                       |
| -------------------------------------------------------------- | -------------------------------------------- |
| Time for doctor to finish SOAP + Rx on a routine visit         | Under 3 minutes                              |
| Secretary can book, queue, and invoice without a second system | Day one                                      |
| No-show rate vs clinic baseline                                | Down via reminders                           |
| Assistant used for book or SOAP draft                          | Optional; screens always work if chat is off |
| Data loss                                                      | Zero                                         |
| Uptime (business hours, Asia/Manila)                           | ≥99.5%                                       |

---

## 5. Scope Overview

| Tier                                | Meaning                                             | Sections   |
| ----------------------------------- | --------------------------------------------------- | ---------- |
| **Core (must ship, clinic-facing)** | Daily loop                                          | §6.1–§6.12 |
| **AI (must ship, scoped)**          | Staff chat assistant + SOAP draft                   | §8, §9     |
| **Phase 2+ (hidden)**               | Built in code, not in clinic UI or this MVP promise | §14        |

---

## 6. Core Modules (MVP)

### 6.1 Authentication & Clinic Setup

- Email/password login, JWT access + refresh. Optional Google OAuth stays if already shipped.
- Doctor profile: name, specialty, PRC license, signature image (Rx/certs), photo
- Clinic profile: name, logo, license, address, contact
- Working hours and holidays (block booking)
- Default appointment duration; service fee list (consult, follow-up, procedures, medicine sold on site)
- **Onboarding:** clinic → doctor → hours → fees → invite secretary (or skip). No rooms, no second doctor, no organization.
- Signup still creates an Organization row under the hood (SaaS tenancy). Clinic staff do not see Organization or Add clinic.

### 6.2 Today

- Today's appointments and live status
- Waiting patients
- Completed today
- Revenue today (simple)
- Outstanding balances
- Failed reminders
- Open HMO claims
- Quick actions: new appointment, walk-in, open assistant
- Mini calendar
- **No** recall-campaign card

### 6.3 Patient Management

- ID, name, birthdate, age, sex, civil status, occupation, contact, email, address, emergency contact, HMO/insurance fields
- Allergies (structured), medical / family / surgical history, current meds, chronic conditions, vaccines, vitals, running chart summary
- File attachments on R2 via presigned URLs
- Fast fuzzy search (name / contact / ID)
- Lookup-before-create duplicates; owner can merge; CSV import for the owner
- Records tab: saved SOAP charts, labs, and files. Documents tab: certificates and referral letters. Timeline lists prescriptions, invoices, and documents.

Patient name / contact / ID search is the clinic search. Semantic chart search is not a Patients tab.

### 6.4 Appointment Scheduling

**Views:** list and calendar (day / week / month). One doctor. No per-doctor columns, no room field, no waitlist.

**Details:** patient, date, time, duration, reason, notes, service type.

**Appointment status:** `Scheduled → Confirmed → Cancelled / No Show / Rescheduled`

**Visit status:** `Arrived → In Consultation → Completed`

**Features:** drag reschedule, walk-in (straight to Arrived), optional recurring series, double-book block (`btree_gist` per doctor), optional public booking link (slot picker only).

Public bookings that are not auto-confirmed sit in a review list on Schedule.

### 6.5 Consultation Records (SOAP)

- Subjective, Objective, Assessment, Plan
- Diagnosis (free text + optional ICD-10)
- Visit vitals, treatment plan, follow-up date (stored on the note; no recall-campaign hub)
- Linked prescriptions and visit attachments
- Chart versioning: every save is a new version; never overwrite in place
- Specialty templates: **general, dental (odontogram), pediatric, OB-GYN, family/internal med, ENT**. Psychiatry and dermatology templates may remain in code; they are not marketed.
- Doctor signature on finalize; print/export PDF
- AI SOAP draft streams into the form; doctor confirms before save

### 6.6 Prescriptions (e-Rx)

- Pad: drug, generic, dosage, form, frequency, duration, quantity, instructions
- Multiple lines; allergy / current-med flags before sign
- PRC, signature, and letterhead on PDF
- History per patient; reuse as a refill template
- **Not in MVP:** send to a pharmacy network

### 6.7 Billing & Payments

- Itemized invoice: consult, procedures, labs, medicine dispensed, other
- Payment: cash, GCash, card, bank transfer (manual entry)
- Partial pay / outstanding balances
- **HMO / PhilHealth:** claims list (`draft` / `submitted` / `approved` / `denied` / `paid`), eligibility checks, LOA request timeline. Payer directory in Settings → Payers. Manual adapter only (no live insurer EDI).
- Credit notes for refunds after payment. Paid invoices cannot be voided.
- Clinic invoice list, search, status filter, CSV export
- Receipt PDF with sequential numbering (`OR-000001` by default)
- **Not in this MVP UI:** BIR PTU/CAS accreditation fields and banners. Receipt numbering stays.

### 6.8 Document Generation

- Medical certificates, referral letters, lab/imaging requests
- Letterhead, signature, license
- Clinic-editable templates
- Certificates and referral letters on the patient **Documents** tab. Lab results and files on **Records**.

### 6.9 Reminders

- Email confirm on booking
- Email reminder 24h before; optional same-day
- Reschedule / cancel notices
- Per-patient opt-out
- Staff list of pending / sent / failed / retry
- Email always on. SMS stays clinic opt-in if already wired.
- Staff bell for in-app alerts stays
- **Not in this MVP UI:** recall campaigns, WhatsApp / Messenger / Viber

### 6.10 Reports

- Appointments: booked vs completed vs no-show by day/week/month
- Revenue by day/week/month and service
- CSV export
- Activity log for the owner (who changed what). Not a second product.

### 6.11 Roles, permissions, audit

| Role                              | Scheduling   | Demographics | SOAP               | Rx   | Billing / HMO | Settings |
| --------------------------------- | ------------ | ------------ | ------------------ | ---- | ------------- | -------- |
| **Owner**                         | Full         | Full         | Full               | Full | Full          | Full     |
| **Reception**                     | Full         | Full         | No (optional view) | No   | Full          | None     |
| **Doctor** (API only in this MVP) | Own calendar | Full         | Own notes          | Own  | View own      | None     |
| **Admin** (API only in this MVP)  | Full         | Full         | View               | View | Full          | Full     |

Every mutation writes `activity_log`. The log is not editable in the app.

### 6.12 Settings (thin)

- Account (password, sessions)
- Doctor profile
- Clinic details, hours, branding
- Services and fees
- Payers
- Receipt numbering
- Document templates
- Team (invite secretary)
- Notification prefs
- Assistant on/off
- Read-only billing plan

**Hidden:** rooms, BIR/growth compliance, membership plans, organization / add clinic.

### 6.13 Platform Super Admin (internal)

Not a clinic-facing module. `/platform` stays so we can run tenants, plans, and the AI kill switch. Cross-clinic metrics are counts only. No patient content.

---

## 7. Why these stay

1. **One doctor + secretary** — the user we are building for. Multi-doctor is Phase 2.
2. **Onboarding** — empty dashboard without hours/fees fails on day one.
3. **Public booking link** — optional; secretary can still book by phone. Slot picker only (no patient chatbot).
4. **Waiting room** — secretary needs to know who is here now.
5. **Patient search** — required once the roster is more than a page.
6. **Email reminders** — the simple no-show lever.
7. **Chart versioning** — medical records are not overwritten.
8. **Specialty templates** — listed specialties are not served by one blank SOAP.
9. **Prescriptions** — legal document; paper Rx is a stated problem.
10. **Billing + HMO** — money and PH payer paperwork are stated problems.
11. **Certificates / referrals** — daily paper the clinic still types in Word.
12. **Roles + audit** — secretary must not edit SOAP; the log is trust.
13. **Simple reports** — revenue and no-shows without a BI product.

---

## 8. Modern & AI Features

### 8.1 AI Clinic Assistant (required)

Chat on every staff screen. Can look up a patient, book/reschedule, draft SOAP, check a balance, and help with invoices/HMO. Same role as the signed-in user. See §9.

This is a **helper on simple screens**, not a replacement for the dashboard.

### 8.2 AI SOAP draft & transcription

Dictate or type a short note; structured SOAP streams into the form. Doctor confirms before save. Transcription stays if already shipped.

### 8.3 AI chart search

Not a clinic tab. Find the patient in Directory, then open Records on the chart. The API and assistant tool remain for later.

### 8.4 AI clinical safety on Rx

Deterministic allergy / interaction flags first. AI may explain the flag. Doctor always confirms.

### 8.5 AI billing assist

Extract amount/date from an uploaded receipt or HMO letter; staff confirms. Never auto-posts money.

### 8.6 UX

- Command palette (Cmd/K)
- Assistant cards (patient, appointment, invoice) instead of walls of text
- Tablet-usable (375–1024px+, 44×44 touch)
- PWA install for a front-desk tablet

### 8.7 Deferred AI / modern

Patient-facing booking FAQ bot, visit-summary auto-send, live voice receptionist, telemedicine, differential diagnosis. See §14.

---

## 9. AI Clinic Assistant

Authoritative implementation catalog: [`docs/architecture/ai-clinic-assistant.md`](./architecture/ai-clinic-assistant.md).

A staff chat panel. It answers and **executes real actions**, never more than that user's role allows.

**Tiers (server-computed, never model-decided)**

| Tier      | Meaning                        | Examples                                                                 |
| --------- | ------------------------------ | ------------------------------------------------------------------------ |
| 0 read    | No writes                      | Search patient, list today, check balance, draft SOAP text               |
| 1 auto    | Low blast, visible "done" card | Harmless status move                                                     |
| 2 confirm | Proposal until Confirm         | Book/cancel, save SOAP, issue Rx, invoice line, send reminder, HMO write |

Always Tier 2: clinical writes, patient messages, billing/HMO writes.

**Safety:** RBAC re-check per tool from the real JWT; re-check DB state before write; ground facts against tool results; `activity_log` with `actor_type = ai_assistant`; kill switch (platform + clinic); daily usage cap.

Representative tools stay as shipped: `search_patients`, `get_patient`, `list_appointments`, `get_available_slots`, `check_patient_balance`, `propose_book_appointment`, `propose_reschedule_appointment`, `propose_cancel_appointment`, `draft_soap_note`, `propose_save_soap_note`, `propose_issue_prescription`, `propose_create_invoice_line`, HMO/eligibility helpers, `propose_send_reminder`, `propose_generate_document`.

The patient-facing booking assistant stays in code. It is **not** shown on `/book/:slug` in this MVP.

---

## 10. Non-Functional Requirements

- HTTPS; JWT; server-side RBAC on every endpoint
- PHI never in plaintext logs or Sentry
- Philippine Data Privacy Act; consent at intake
- Daily backups; R2 via presigned URLs
- Double-book block at the database
- Waiting-room WebSocket degrades to polling
- Assistant failure never blocks the manual screen
- Every screen 375px+; printable Rx / cert / invoice / SOAP
- PHI-scrubbed error tracking

Offline write-and-sync is Phase 2. A connectivity drop should not silently fail a book/bill/Rx.

---

## 11. Data Model

Tables for kept modules (prescriptions, invoices, payments, documents, reminders, SOAP versions, assistant conversations) stay as shipped. See [`docs/architecture/data-model.md`](./architecture/data-model.md).

Deferred tables (`patient_recalls` campaigns, membership plans, portal tokens, NPS, organizations UI) are **not dropped**. Clinic UI does not link to them.

`activity_log` remains the shared audit surface for staff and assistant writes.

---

## 12. Production Readiness Checklist

**Core**

- [ ] New clinic completes onboarding with no engineering help
- [x] Book → arrive → SOAP + Rx → bill → pay (`test_patient_lifecycle.py`)
- [x] Double-book impossible under concurrent requests
- [ ] Printables render on paper (manual gate)

**Data safety**

- [ ] Backup + restore drilled
- [x] SOAP versions immutable
- [x] Reception cannot read SOAP unless opted in

**AI**

- [x] Tier 2 requires confirm in tests
- [x] Tool errors do not half-write
- [x] Usage cap and kill switch

**Trust**

- [x] Consent at intake
- [ ] No PHI in prod logs (spot-check)
- [x] `activity_log` on service mutations

**Ops**

- [ ] Uptime alerting before first pilot
- [x] Support + rollback docs in `deployment.md`

---

## 13. Build Order / Remaining work

Phases 0–43 already shipped the modules. Remaining product work is **not new modules**:

1. **Solo-clinic surface** (this change) — hide Phase 2 UI; rewrite this PRD; keep APIs
2. **Design overhaul Phases 44–47** — hierarchy, then redesign **kept** screens only (Today, Schedule, Waiting, Patients, SOAP/Rx, Billing/HMO, Documents, Reminders, Reports, Settings thin, Assistant). Do not polish hidden screens.

Do not start Phase 2 multi-doctor, portal, WhatsApp, or BIR-depth work until this MVP is in a pilot clinic.

---

## 14. Out of Scope for MVP (Phase 2+)

Code may exist. Clinic nav, onboarding, and this PRD do not promise them.

| Deferred                                                                                              | Why later                                                                                                           |
| ----------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------- |
| **Multi-doctor clinic** (shared front desk, per-doctor columns, extra-doctor invite, rooms, waitlist) | Stated target is 1 doctor + secretary. Data model already allows `doctor_id`; UI stays single-doctor until Phase 2. |
| Multi-clinic organizations / add-clinic / workspace hopping                                           | One clinic per pilot. Org rows stay for SaaS billing.                                                               |
| Patient self-service portal                                                                           | Staff app only.                                                                                                     |
| Patient-facing booking FAQ chatbot                                                                    | Public page is a slot picker.                                                                                       |
| Semantic chart search tab                                                                             | Search the patient by name, then open Records on the chart. API stays.                                              |
| Recall campaigns                                                                                      | Follow-up date can live on SOAP; no campaign hub.                                                                   |
| WhatsApp / Messenger / Viber                                                                          | Email first.                                                                                                        |
| NPS, Google review requests, membership plans, BNPL, FHIR, referral chart-share                       | Growth extras.                                                                                                      |
| BIR PTU/CAS depth                                                                                     | Receipt numbering is enough for this MVP.                                                                           |
| Live HMO/PhilHealth EDI                                                                               | Manual claims / eligibility / LOA stay.                                                                             |
| Inventory, LIS, APE/corporate volume, Dashlabs-style multi-station queue                              | Wrong segment.                                                                                                      |
| Offline write-and-sync                                                                                | Online desk.                                                                                                        |
| Live voice receptionist, telemedicine, AI diagnosis                                                   | Out of the daily loop.                                                                                              |
| Native iOS/Android                                                                                    | PWA covers tablet.                                                                                                  |

**Internal keep:** Super Admin, pricing, tenancy, feature flags.

---

## 15. Open Questions

1. **SMS cost** — clinic pays per SMS vs bundled. Email reminders ship regardless.
2. **AI cost** — subscription vs usage add-on. Daily cap is already technical.
3. **E-signature** — uploaded signature image vs legally binding e-sign. Image is enough to start.
4. **Pilot clinics** — first 2–3 solo practices; any CSV import needed?
5. **Medicine on site** — invoice line type is enough; no stock module.

activity-log: N/A — this document change does not mutate clinic data.
