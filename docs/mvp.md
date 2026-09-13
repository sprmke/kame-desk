# KameDesk — MVP Product Requirements Document

**Product:** DoctorDesk
**Tagline:** _Your Clinic. Simplified._
**Version:** 1.1 (MVP, refined)
**Status:** Draft — supersedes the v1.0 outline pasted into planning; scope reviewed and expanded
**Last updated:** 2026-09-08

Related docs: [`tech-stack.md`](./tech-stack.md) (authoritative technology choices — this doc does not redefine stack decisions, it defines _what to build_), [`README.md`](./README.md) (index, product scope one-liner).

> This document is the single source of truth for **what ships in the DoctorDesk MVP**. When scope changes during implementation, update this file in the same change — do not let the code and this doc drift.

---

## Table of contents

1. [Executive Summary](#1-executive-summary)
2. [Problem Statement](#2-problem-statement)
3. [Target Users](#3-target-users)
4. [Product Goals & Success Metrics](#4-product-goals--success-metrics)
5. [Scope Overview](#5-scope-overview)
6. [Core Modules (MVP)](#6-core-modules-mvp)
7. [Gaps We Are Closing (missed in the original outline)](#7-gaps-we-are-closing-missed-in-the-original-outline)
8. [Modern & AI Features](#8-modern--ai-features)
9. [AI Clinic Assistant — Architecture Spec (flagship feature)](#9-ai-clinic-assistant--architecture-spec-flagship-feature)
10. [Non-Functional Requirements](#10-non-functional-requirements)
11. [Data Model Additions](#11-data-model-additions)
12. [Production Readiness Checklist](#12-production-readiness-checklist)
13. [Build Order / Phasing](#13-build-order--phasing)
14. [Out of Scope for MVP (Phase 2+)](#14-out-of-scope-for-mvp-phase-2)
15. [Open Questions & Decisions Needed](#15-open-questions--decisions-needed)

---

## 1. Executive Summary

DoctorDesk is a cloud-based clinic management platform built for independent doctors and small clinics. It combines patient records, appointment scheduling, consultation documentation (SOAP/EMR), prescriptions, billing, document generation, and patient communication into a single platform — and layers an **AI Clinic Assistant** on top so most of that work can be done by _asking_, not by clicking through a dashboard.

The MVP's bar is not "a demo of every module." The bar is: **a solo doctor or small clinic can fully replace their current paper/spreadsheet/Viber workflow with DoctorDesk on day one**, safely, and the app can be operated hands-free through the AI assistant for the highest-friction daily tasks (booking, rescheduling, drafting notes, chasing balances, sending reminders).

## 2. Problem Statement

Many clinics still run on a combination of paper charts, spreadsheets, messaging apps (Viber/Messenger), and handwritten prescriptions. This causes:

- Lost or incomplete patient records
- Missed or double-booked appointments
- Time-consuming administrative work that eats into consultation time
- Manual, easy-to-forget follow-ups and reminders
- Duplicate or conflicting patient information across tools
- No visibility into revenue, no-show rates, or outstanding balances
- Slow, error-prone document creation (certificates, referrals, receipts)
- Poor patient experience (no confirmation, no reminders, no self-service)

DoctorDesk replaces all of the above with one platform, and removes the _manual data-entry tax_ specifically with an AI assistant that can execute the same actions a front-desk staffer would.

## 3. Target Users

**Primary users**

- General Practitioners, Specialists, Dentists, Pediatricians, Dermatologists, OB-GYN, Internal Medicine, Family Medicine, Psychiatrists

**Secondary users**

- Small clinics (2–5 doctors sharing a front desk)
- Clinic assistants / medical secretaries / receptionists

**Personas (for MVP prioritization)**

| Persona                                          | Context                                                     | What they need most from MVP                                                       |
| ------------------------------------------------ | ----------------------------------------------------------- | ---------------------------------------------------------------------------------- |
| **Solo doctor, no staff**                        | Runs their own booking, own notes, own billing              | AI assistant to do front-desk work they don't have time for; fast SOAP entry       |
| **Doctor + 1 receptionist**                      | Receptionist manages calendar/patients; doctor writes notes | Clear RBAC split; receptionist should never see full clinical notes unless allowed |
| **Small clinic, 2–5 doctors, shared front desk** | Multiple calendars, one waiting room                        | Per-doctor scheduling, shared patient registry, room/resource awareness            |

## 4. Product Goals & Success Metrics

### Goals

- Digitize clinic operations end-to-end (no parallel paper/spreadsheet system needed)
- Reduce administrative time per patient visit
- Improve appointment management and cut no-shows
- Organize patient medical records in one searchable place
- Simplify documentation (SOAP notes, prescriptions, certificates)
- Improve patient communication (reminders, confirmations, self-service booking)
- Generate professional, printable documents (Rx, certificates, receipts, referrals)
- Let an AI assistant execute routine dashboard work through conversation, not just answer questions

### Success metrics (track from week 1 of pilot clinics)

| Metric                                                                                                                                  | Target for MVP pilot                                                          |
| --------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------- |
| No-show rate                                                                                                                            | Reduce by ≥25% vs. clinic's pre-DoctorDesk baseline (via automated reminders) |
| Time to complete a visit's paperwork (SOAP + Rx + billing)                                                                              | Under 3 minutes doctor-side for a routine visit                               |
| % of appointments booked without a phone call (self-service link or AI assistant)                                                       | ≥30% within first 60 days                                                     |
| % of eligible routine actions (reschedule, reminder send, note draft) completed via the AI assistant instead of manual dashboard clicks | ≥40% of eligible actions within 90 days                                       |
| Doctor weekly active usage                                                                                                              | ≥5 sessions/week per active doctor                                            |
| Data loss / record-loss incidents                                                                                                       | Zero                                                                          |
| Uptime (business hours, Asia/Manila)                                                                                                    | ≥99.5%                                                                        |

These metrics also define what "AI Assistant success" looks like — it is not a novelty chat window, it is measured by how much manual dashboard work it actually removes.

## 5. Scope Overview

| Tier                                | Meaning                                                            | Sections              |
| ----------------------------------- | ------------------------------------------------------------------ | --------------------- |
| **Core (must ship)**                | Original outline modules, completed and hardened                   | §6.1–§6.5             |
| **Closing the gap (must ship)**     | Necessary for a clinic to go live without a parallel manual system | §6.6–§6.12, all of §7 |
| **Modern / AI (must ship, scoped)** | Differentiators, including the flagship AI assistant               | §8, §9                |
| **Phase 2+ (explicitly deferred)**  | Real but not required for MVP usability                            | §14                   |

## 6. Core Modules (MVP)

### 6.1 Authentication & Clinic Setup

- Secure login (email/password + optional Google OAuth), JWT access + refresh tokens (per `tech-stack.md`)
- Doctor profile: name, specialty, PRC license number, signature (uploaded image, used on Rx/certs), photo
- Clinic profile: name, logo, license/accreditation info, address, contact number, email
- Working hours per day, holiday schedule (blocks booking automatically)
- Default appointment duration (per doctor, overridable per appointment type)
- Consultation fees (base fee, follow-up fee, per-service fee list)
- Multi-doctor support within one clinic (shared front desk, per-doctor calendars) — **added scope**, see §7.1
- Roles at setup time: `owner`, `admin`, `doctor`, `reception` (per `tech-stack.md`)
- **First-run onboarding wizard**: clinic profile → doctor profile → working hours → fees → invite staff → done. Without this, a new clinic has nothing to click on day one — **added scope**, see §7.2
- **Organizations (multi-clinic envelope)** — Phase 41: signup creates an **Organization** (billing/ownership unit) plus the first **Clinic** (operational/PHI unit). An org owner may add more clinics under the same org; plan and doctor seats pool at org level with per-clinic enrollment. **Strict PHI isolation**: each clinic keeps its own patient registry; org surfaces show aggregate counts only, never patient content.

### 6.2 Dashboard

Displays:

- Today's appointments (with live status)
- Upcoming appointments (next 7 days)
- Waiting patients (live queue, see §7.4)
- Completed consultations today
- Revenue summary (today / week / month)
- Pending follow-ups (patients due for a recall)
- Outstanding balances (added scope, see §6.7)
- Quick actions: new appointment, new walk-in, new patient, open AI assistant
- Calendar overview (mini month view)
- **AI assistant launcher** — floating entry point, always available from the dashboard (see §9)

### 6.3 Patient Management

**Patient profile**

- Patient ID (auto-generated), Full Name, Birthdate, Age (computed), Sex, Civil Status, Occupation
- Contact Number, Email Address, Address
- Emergency Contact (name, relationship, number)
- Insurance/HMO (provider, member ID, coverage notes)

**Medical information**

- Allergies (structured list, not free text — required for AI drug-interaction checks, see §8.6)
- Medical History, Family History, Surgical History
- Current Medications, Chronic Conditions
- Vaccination History
- Vital Signs (height, weight, BMI computed, BP, temp, HR, RR, SpO2)
- Clinical Notes (free text, distinct from SOAP visit notes — a running chart summary)

**File attachments**

- Laboratory Results, X-rays, Ultrasound, MRI/CT Scan, Images, PDFs, other documents
- Stored in object storage (Cloudflare R2), served via presigned URLs — never public
- Each file tagged with type, date, and (optionally) linked to a specific visit

**Patient search** — global, fast, fuzzy match on name/contact/patient ID (added scope, see §7.5)

**Dedupe and import (Phase 23)**

- Lookup-before-create shows possible matches by name or contact
- Owner/admin can merge a duplicate into the kept chart (related records move; source is archived)
- Owner/admin can import patients from CSV after a dry-run preview
- Medical fields (allergies, medications, conditions, vaccines, HMO) have structured forms, not a JSON textarea
- Patient detail includes a timeline of visits, prescriptions, invoices, and documents

### 6.4 Appointment Scheduling

**Views:** Daily, Weekly, Monthly (per-doctor and clinic-wide toggle)

**Appointment details:** Patient, Date, Time, Duration, Reason for Visit, Notes, Assigned Doctor, Room/resource (if clinic has more than one consult room)

**Appointment status (pre-visit lifecycle):**

`Scheduled → Confirmed → Cancelled / No Show / Rescheduled`

**Visit status (day-of lifecycle, once the patient is at the clinic):**

`Arrived → In Consultation → Completed`

Terminal/exception states apply at any point: `Cancelled`, `No Show`, `Rescheduled`. This two-lifecycle split (appointment vs. visit) resolves the ambiguity in the original outline's single flat status list and matches how a front desk actually thinks about a booking (before the day) vs. a visit (the day itself).

**Scheduling scale (Phase 24)**

- Doctor pickers show the doctor's name
- Appointment type comes from the service catalog (duration default)
- Rooms have a Settings UI and can be set on a booking
- Calendar can show one column per doctor
- Public bookings that are not auto-confirmed sit in a review queue
- Staff can waitlist a patient for an earlier slot
- Appointment list filters by search, status, doctor, and date range

**Features:**

- Drag-and-drop scheduling and rescheduling
- Walk-in appointments (skip straight to `Arrived`)
- Recurring appointments (e.g. weekly physical therapy, monthly follow-up)
- Double-booking prevention (Postgres exclusion constraint per doctor/room — hard DB-level guarantee, not just UI validation)
- Color-coded appointments (by status and/or by doctor)
- **Public self-service booking link** (added scope, see §7.3) — patients can request an appointment without calling
- **Automated reminders** (added scope, see §7.6) — SMS/email at booking, 24h before, and (optionally) 2h before

### 6.5 Consultation Records (EMR)

**SOAP documentation**

- **Subjective** — patient-reported symptoms, history of present illness
- **Objective** — exam findings, vitals (pulled from patient vitals or entered fresh for this visit)
- **Assessment** — diagnosis (free text + optional ICD-10 code lookup)
- **Plan** — treatment plan, prescriptions issued, orders placed, follow-up

**Additional per-visit information**

- Diagnosis (primary + secondary, optional ICD-10 codes)
- Vital signs for this visit
- Treatment plan
- Follow-up date (feeds the dashboard's "pending follow-ups" and the recall/reminder system, §7.7)
- Prescriptions issued during this visit (linked, see §6.6)
- Lab/imaging orders placed during this visit, tracked as `clinical_orders` (`ordered` → `in_progress` → `resulted` / `cancelled`) with result text and optional file link
- Visit-specific attachments (e.g. a photo of a wound, an in-clinic ECG strip)
- **Chart versioning** — every save creates a new version row; SOAP notes are never overwritten in place. This is a compliance and safety requirement, not a nice-to-have (added scope, see §7.8)
- **Specialty templates** — general, dental (real interactive odontogram, not just a template line — see below), pediatric (height/weight/percentile), OB-GYN (gravida/para/LMP/EDD), psychiatry (MSE/risk), dermatology (location/morphology)
- **Dental charting (Phase 39, added scope)** — for the dental template, a first-class 32-tooth adult (FDI numbering) interactive odontogram, not just a SOAP template line, matching how dedicated dental PM systems treat it: click a tooth/surface to record a condition (caries, filled, missing, crown, root canal, extraction planned, impacted, fractured), findings are append-only per-patient history (not per-visit — progression like caries → filled → crown stays visible across visits), and a `planned` finding can be pushed straight to the visit's invoice as a line item without re-typing it. Primary/deciduous dentition and full periodontal charting (pocket depths, bleeding indices) are explicitly out of scope for this phase.
- **Version diff** — compare two SOAP versions field by field
- Doctor e-signature on the finalized note (image signature applied at save time)
- Print/export the full consultation note as PDF

### 6.6 Prescriptions (e-Rx) — _added module, missing from original outline_

A prescription is a legal document; DoctorDesk cannot claim MVP-completeness without it.

- Prescription pad: drug name, generic name, dosage, form, frequency, duration, quantity, special instructions
- Multiple drugs per prescription
- Pulls from the patient's allergy list and current medications to flag conflicts before the doctor signs (see §8.6, AI-assisted, doctor always confirms). Drugs outside the curated `drug_reference` list show an explicit **not checked** flag and do not require an override.
- Doctor PRC license number, signature, and clinic letterhead auto-populated on the printed/PDF Rx
- Printable and downloadable PDF, formatted for standard Rx paper size
- Prescription history per patient (list of all past prescriptions, reusable as a template for refills)
- **Not building in MVP:** e-Rx submission directly to pharmacies (needs pharmacy-network integration, Phase 2)

### 6.7 Billing & Payments — _added module, missing from original outline_

A clinic cannot go live without knowing who owes what.

- Itemized invoice per visit: consultation fee, procedures, lab fees, medicine dispensed (if the clinic sells meds on-site), other fees
- Payment recording: cash, GCash, card, bank transfer — manual entry for MVP (no live payment gateway required to launch)
- Partial payment / balance tracking per patient
- HMO/insurance claims as a clinic-wide status list (`draft` / `submitted` / `approved` / `denied` / `paid`), each tagged with a payer type (HMO / PhilHealth / self-pay / other). No live insurer EDI — submission is tracked in-app behind a pluggable claims-partner adapter (Phase 33), MVP ships the manual adapter only.
- Structured HMO/PhilHealth eligibility checks (payer, member ID, verified amount, status) and LOA (Letter of Authorization) requests with a request → submitted → approved/denied status timeline, replacing free-text claim notes (Phase 33). Claims, eligibility, and LOA are peer tabs of the Billing hub, each a searchable, sortable, paginated list with its own create modal. The clinic payer directory that feeds their payer-name autocomplete is clinic configuration and lives in Settings → Clinic → Payers.
- Credit notes (`CN-`) for refunds or adjustments after payment. Paid invoices cannot be voided.
- Clinic-wide invoice list with search, status filter, and CSV export
- Receipt generation (PDF), sequential receipt numbering per clinic (configurable to match local requirements, e.g. BIR Official Receipt numbering in the Philippines)
- BIR compliance depth (Phase 34): clinic declares its own TIN, registered business name/address, VAT registration status, and compliance mode (not yet accredited / Permit to Use / Computerized Accounting System) with accreditation number and validity date. Receipts/invoices render TIN, registered identity, permit/accreditation number, and a VAT breakdown (vatable sales / 12% VAT) when VAT-registered, or a "non-VAT, not valid for claim of input tax" disclosure when not. Accreditation with BIR stays each clinic's own responsibility — kame-desk provides the fields, not the filing. A non-blocking banner on the Billing page flags incomplete or expired compliance fields; it never blocks invoice issuance.
- Daily/weekly/monthly revenue reports (feeds the dashboard revenue summary)
- Outstanding balance list, sortable, exportable

### 6.8 Document Generation — _added module, missing from original outline_

Clinics generate a steady stream of non-Rx paperwork; this is a top reason clinics still keep a typewriter or Word template folder.

- Medical certificates (fit-to-work, fit-to-travel, medical excuse)
- Referral letters to specialists, with recipient, status (`draft` / `sent` / `acknowledged` / `completed`), and outcome (not PDF-only)
- Laboratory / imaging request forms
- Certificate of confinement / consultation (as applicable to specialty)
- Clinic-branded letterhead, doctor signature and license auto-filled
- Template library, editable per clinic, with placeholders auto-filled from patient/visit data
- All generated documents saved to the patient's file attachments automatically (audit trail of what was issued and when)

### 6.9 Patient Communication & Reminders — _added module, missing from original outline_

- Appointment confirmation (SMS/email) sent immediately on booking
- Reminder 24 hours before the appointment; optional same-day reminder
- Reschedule/cancellation notifications
- Follow-up/recall reminders (driven by the SOAP "Follow-up Date" field and by chronic-condition recall rules)
- Two-way: patient can confirm/cancel/request reschedule by replying to the reminder or via the self-service link (§7.3); on WhatsApp, tapping the Confirm/Cancel quick-reply button on the reminder message does the same thing
- Delivery channel: email always available; SMS via Twilio (clinic opt-in, cost-metered; same pattern already decided in `tech-stack.md`); WhatsApp via Meta's WhatsApp Business Cloud API (Phase 35, clinic opt-in, cost-metered) — sent as pre-approved message templates, per Meta's requirement for business-initiated messages. Messenger and Viber exist as adapter stubs behind the same channel interface, not wired to a live API yet — validate WhatsApp with real pilot clinics before building those out.
- Staff reminder dashboard: pending/sent/failed/cancelled, retry a failed send
- Staff in-app alert inbox (Phase 40): bell + persisted feed for bookings, visit flow, billing, messaging, and team events; realtime via clinic WebSocket; separate from patient reminder settings
- Per-patient reminder opt-out
- High no-show risk moves the 24h reminder to 36h before and the same-day reminder to 6h before

### 6.10 Reports & Analytics — _added module, missing from original outline_

- Appointments: booked vs. completed vs. no-show, by day/week/month, by doctor name (not UUID). Bars open the appointment or invoice list with the same range.
- Revenue: by day/week/month, by service type, by doctor
- Patient growth: new vs. returning patients over time
- Top diagnoses / visit reasons (useful for a clinic to spot trends)
- Exportable to CSV for accounting handoff

### 6.11 Roles, Permissions & Audit Log — _added module, missing from original outline_

The original outline never defines who can see what. This is not optional for a medical records product.

| Role          | Scheduling          | Patient demographics | Clinical notes (SOAP)                                                    | Prescriptions       | Billing         | Clinic settings |
| ------------- | ------------------- | -------------------- | ------------------------------------------------------------------------ | ------------------- | --------------- | --------------- |
| **Owner**     | Full                | Full                 | Full (their own clinic)                                                  | Full                | Full            | Full            |
| **Admin**     | Full                | Full                 | View only (never edit clinical content)                                  | View only           | Full            | Full            |
| **Doctor**    | Full (own calendar) | Full                 | Full (own patients)                                                      | Full (own patients) | View own visits | None            |
| **Reception** | Full                | Full                 | **No access** by default (configurable per clinic to allow limited view) | No access           | Full            | None            |

- Every mutation (patient edit, SOAP save, Rx issued, invoice created, appointment status change) writes to an append-only `activity_log` — who did what, when, to which record. Required for both trust and any future compliance audit.
- Doctors and admins can view the activity log for their own clinic; it is never editable or deletable through the app.

### 6.12 Settings — _rounds out §6.1_

- Notification preferences (which reminders are on, lead time)
- Data export (patient list, appointment history as CSV) and a clinic deletion-request path (records the request; does not wipe PHI immediately)
- Account recovery: forgot/reset password, email verification, session list, sign out everywhere
- Clinic billing plan (read-only in-app; Super Admin changes the plan)

### 6.13 Platform Super Admin — _added for SaaS operation_

- Tenant `status` (`trial` / `active` / `suspended` / `cancelled`) and `plan_key` (`starter` / `pro` / `clinic`)
- Super Admin allow-list (`PLATFORM_ADMIN_EMAILS`), `/platform` shell, public `/pricing`
- Feature flag kill switch for the AI assistant (DB overrides env)
- Audited support login (30 minutes, clinic-app banner)
- Cross-clinic metrics are counts only. No patient content.
- Working-hours/holiday overrides (already in §6.1, surfaced here for ongoing edits, not just first-run)
- Services and fees catalog, reception SOAP access, BIR receipt numbering, document template placeholders and sample preview

### 6.14 Patient self-service portal — _added module, pulled forward from Phase 2 deferral_

A separate, clinic-scoped login for patients themselves, independent of the staff app shell — no shared route, component, or auth token with the clinic-user/admin app.

- Login is a magic link (email or SMS, whichever matches the contact info on file), not a password — a new `PatientPortalToken` (hashed, single-use, 15-minute TTL) modeled on the staff `AccountToken` pattern, not the weaker `Reminder.reply_token` pattern used for confirm/cancel taps.
- A verified session is a short-lived (30 min) `patient_access` JWT with the clinic id baked into its claims at issuance — no runtime clinic switching, since a patient portal session is always single-clinic.
- Scope is intentionally narrow: own visit history, a chart summary (diagnoses, ICD-10 codes, follow-up dates, vitals trend) — never the raw SOAP subjective/objective/plan text — invoices/balance, and document downloads via the same R2 presigned-URL pattern staff use. No messaging to the doctor, no self-edit of clinical data, no lab-result upload.
- A consent notice appears on first login, acknowledged once per browser.
- `activity_log`: `patient_portal.login`, `patient_portal.document_downloaded`.

### 6.15 Growth & retention differentiators — _added module, backlog phase 38_

Small, individually incremental items grouped into one phase because each is too small to justify its own build slot.

- **Reputation management**: post-visit trigger (visit marked Completed) queues a "request a review" prompt carrying the clinic's Google Business review link, sent over the existing email/SMS/WhatsApp channel infra. Settings toggle to enable/disable plus the review link itself. `activity_log`: `review_request.sent`.
- **Patient satisfaction / NPS micro-survey**: a one-question 0-10 NPS prompt (+ optional comment) sent alongside the review request, same channel infra, single-use reply link (`/nps/{token}`, no login). Reportable as an NPS trend on the Reports dashboard (promoters ≥9, detractors ≤6, score = (promoters − detractors) / responded × 100).
- **Doctor-to-doctor referral chart sharing**: a referral letter document (§6.8) can generate a scoped, expiring (7-day) share link to a read-only chart-summary snapshot — same shape as the patient portal's chart summary (§6.14), no recipient account required. `activity_log`: `referral.chart_shared`.
- **Membership / subscription care plans**: clinic-defined recurring plans (name, price, billing interval, included-service visit allowances) that patients enroll in; a matching invoice line item automatically gets a waiver discount while allowance remains for the period. The recurring plan charge itself is recorded as a manual payment (§6.7) — no live recurring-billing gateway.
- **Financing/BNPL hook**: an invoice "Send to financing" action behind a pluggable provider adapter, hidden unless a clinic configures a real provider. No confirmed PH healthcare-specific BNPL partner exists yet, so the default adapter does nothing — this is an honest hook, not a fabricated integration.
- **DOH EMR accreditation flag**: display-only accreditation number + validity date in clinic settings, same pattern as the BIR PTU/CAS fields (§6.12) — a trust signal for patients, not an accreditation workflow.
- **FHIR export**: a read-only, on-demand `GET /patients/{id}/fhir-export` endpoint producing a minimal FHIR R4 `Patient` + `Encounter` bundle, RBAC-gated the same as chart access. Documented as a capability flag, not a live PHIE (Philippine Health Information Exchange) connection — no PHIE sandbox/credentials exist to integrate against.

## 7. Gaps We Are Closing (missed in the original outline)

Summary list of what §6 added beyond the pasted draft, with the reasoning for why each is MVP-required (not Phase 2):

1. **Multi-doctor / shared front desk support** — the original outline reads as single-doctor. Secondary target users are explicitly "small clinics," which means 2+ doctors sharing one front desk and one patient registry from day one. Skipping this would make the MVP unusable for half the stated target audience.
2. **Onboarding wizard** — a brand-new clinic with an empty dashboard and no guided setup will not configure fees/hours/staff correctly and will bounce. Needed for a self-serve MVP.
3. **Public self-service booking link** — every modern comparable product (Calendly-style booking, plus every competing clinic system) offers this; a clinic without it still needs a phone line staffed during business hours, which defeats "reduce administrative work."
4. **Live waiting-room / queue view** — "waiting patients" appears on the dashboard in the original outline but there's no mechanism described to know who is actually waiting right now versus scheduled for later. This needs a real-time queue (WebSocket-driven, matches `tech-stack.md`'s realtime choice).
5. **Global patient search** — a clinic with hundreds of patients cannot function without fast search; this was implied but not specified.
6. **Automated reminders** — the single biggest lever on the "reduce no-shows" goal stated in the original outline's own Product Goals, yet no reminder mechanism was specified.
7. **Recall / follow-up campaigns** — the original outline has a "Follow-up Date" field but nothing that acts on it. A field that nobody reads is not a feature.
8. **Chart versioning** — medical records must never be silently overwritten; this is both a compliance basic and a trust requirement once AI-assisted drafting (§8.2) is in the picture.
9. **Specialty SOAP templates** — the target user list spans dentists, pediatricians, OB-GYN, psychiatrists; a single generic SOAP form serves none of them well.
10. **Prescriptions module** — entirely absent from the pasted outline (it stops mid-sentence in "Consultation Records") despite being one of the most legally load-bearing documents a clinic produces.
11. **Billing & payments** — entirely absent from the pasted outline. A clinic cannot go live without knowing what it charged and what it collected.
12. **Document generation** (certificates, referrals, lab requests) — entirely absent, but a daily-use feature for every target specialty listed.
13. **Roles/permissions & audit log** — entirely absent. Medical software without a defined access model and an audit trail is not production-ready, full stop.
14. **Reports & analytics** — entirely absent. The dashboard cannot show a trustworthy "revenue summary" without a reporting layer behind it.

## 8. Modern & AI Features

DoctorDesk's differentiation is not "another EMR" — it's an EMR a solo doctor can run largely by talking to it. `tech-stack.md` already commits to Gemini/OpenAI, PydanticAI, SSE streaming, ARQ background jobs, and pgvector — this section defines the _product_ features built on that stack, and calls out which patterns are adapted from **kame-homes** (a sibling product in this workspace) where a very similar problem — "give hosts an assistant instead of a dashboard" — has already shipped and been hardened in production.

### 8.1 AI Clinic Assistant (flagship — required for MVP)

The single most important AI feature. A chat panel, available from every screen, that can **answer questions and execute real dashboard actions** — book/reschedule/cancel appointments, look up a patient, draft (never silently send) a reminder, create a billing line item, draft a SOAP note from a description, check a patient's balance, generate a certificate — scoped strictly to the signed-in user's real role and permissions (§6.11).

This is explicitly what the user asked for: _"the AI assistant that will simplify and automate and help our users to chat and talk with our AI instead of manually managing everything from our dashboard."_ Full architecture in §9 — it is a first-class MVP module, not a stretch goal.

### 8.2 AI-Assisted SOAP Drafting & Ambient Transcription

Already decided in `tech-stack.md` (PydanticAI structured output, faster-whisper via ARQ, SSE streaming into the SOAP fields). Product behavior for MVP:

- Doctor can dictate during or after a consultation; audio is transcribed and PydanticAI drafts a structured SOAP note (Subjective/Objective/Assessment/Plan) from the transcript
- Draft streams into the SOAP form field-by-field as it's generated (visible, not a black box)
- **Doctor must review and confirm before save** — the AI never writes a chart version directly. This mirrors kame-homes' rule that AI output is always a draft a human confirms before anything is persisted.
- Doctor can also type a short note ("BP high, refill maintenance meds, follow up 2 weeks") and have the assistant expand it into full SOAP structure

### 8.3 AI Chart Search (semantic)

- After a SOAP note is saved, an embedding is generated (ARQ job, pgvector) so the doctor can search charts by meaning, not just keyword — e.g. "patients with recurring migraines in the last 6 months"
- Search results always link back to the real chart version; the AI never fabricates a chart record

### 8.4 AI Patient-Facing Booking & FAQ Assistant

A lightweight, text-first counterpart to kame-homes' AI voice receptionist, adapted to a clinic's needs and cost profile:

- Embedded in the public self-service booking page (§7.3): patients can type "Can I get a same-day appointment tomorrow morning?" and the assistant checks real availability and books it, instead of a rigid slot picker being the only option
- Answers clinic FAQs (hours, address, what to bring, accepted HMOs) grounded in the clinic's own settings data — never invents clinic policy
- **Explicitly scoped to text chat for MVP, not live voice.** kame-homes' voice receptionist required a dedicated real-time audio pipeline, per-session cost caps, and a multi-phase hardening pass — that is the right pattern to copy _later_ (Phase 2, once volume justifies it, see §14), not to ship in the first release. Applying that lesson now avoids repeating the same "shipped without a kill switch" risk on a smaller budget.
- Same two-layer safety pattern as kame-homes: a guest-safe grounding-facts builder (only clinic hours/services/booking data — never another patient's records) plus an independent safety check on the assistant's output before it's shown.

### 8.5 AI Visit Summary for Patients

- After a visit is marked Completed, generate a short, plain-language summary of what was discussed, any prescriptions, and the follow-up date — sent to the patient alongside (not replacing) the doctor's actual note
- Doctor can edit or suppress before sending; never auto-sent without the option to review

### 8.6 AI-Assisted Clinical Safety Checks

- Drug-interaction and allergy-conflict checks run automatically when a prescription is drafted (§6.6), using the patient's structured allergy/medication data — **deterministic rule/database check first**, AI used only to explain the flag in plain language, never to decide whether to block. This mirrors the kame-homes pattern of "the safety boundary is a deterministic guard, not the prompt."
- Flags are advisory; the doctor can always override with a documented reason (logged to the audit trail, §6.11)

### 8.7 AI Billing / Receipt Assistance

- When a patient submits a receipt or HMO document (e.g. proof of an out-of-pocket lab payment they want reimbursed, or an HMO authorization letter), an AI pass extracts the amount/date/provider and pre-fills the billing entry for staff to confirm — adapted from kame-homes' AI receipt validation for guest payment proofs. Staff always confirms before the entry is finalized; the AI never finalizes a financial record unattended.

### 8.8 No-Show Prediction & Smart Reminder Timing

- Simple, explainable model (not a black box) using appointment history (day of week, lead time booked, past no-show count for that patient) to flag high-risk appointments for an extra reminder or a confirmation call
- Purely additive to the deterministic reminder schedule in §7.6 — never replaces the guaranteed 24h reminder

### 8.9 Modern UX Touches (small, high-leverage)

- **Command palette** (Cmd/Ctrl+K) for fast navigation and search across patients/appointments — same pattern kame-homes uses for its dashboard-wide search
- **Rich chat rendering** in the AI assistant panel — tables, status cards, and confirmation cards instead of walls of text (same `ChatBlock`-style approach as kame-homes, adapted to clinic entities: patient cards, appointment cards, invoice cards)
- Mobile-responsive dashboard (front desk often runs on a tablet) — 375–1024px+, 44×44px touch targets, non-negotiable for a receptionist standing at a counter
- PWA-installable web app (add-to-home-screen for a tablet-based front desk, works with existing hosting choice)

### 8.10 Explicitly deferred from "modern/AI" for MVP

- Live voice AI receptionist (phone-call-quality, speech-to-speech) — Phase 2, see §14, once the text assistant's grounding/safety pattern is proven and the clinic's call volume justifies the added cost/complexity
- Telemedicine video consults
- Wearable / remote patient monitoring integration
- Full clinical decision support (differential diagnosis suggestions) — legally sensitive territory; MVP AI stays scoped to drafting, search, and safety _flags_, never diagnosis suggestions
- Insurance EDI / live claims submission

## 9. AI Clinic Assistant — Architecture Spec (flagship feature)

This section specifies the assistant named in §8.1 in enough detail to build it. The pattern is deliberately modeled on kame-homes' AI Dashboard Assistant (`docs/architecture/ai-dashboard-assistant.md` in that repo) — a chat assistant with a tiered risk model, tool-calling, and a full audit trail that has already been hardened across dozens of real admin actions. DoctorDesk adapts the same _shape_ to its own stack (FastAPI + PydanticAI instead of Deno + Gemini tool-calling client) and its own domain (patients/appointments/SOAP/billing instead of bookings/properties/finance).

### 9.1 What it is

A chat panel embedded in the dashboard (floating launcher, available on every screen per §6.2) that can answer questions and **execute real actions**, strictly scoped to the signed-in user's actual role (§6.11) — never more than the dashboard UI itself would allow that role to do.

**Shipped (Phase 20):** Production requests go through a PydanticAI structured tool planner. The model never writes directly; the existing tier/RBAC/confirm layer executes tools. Tests may still send `__tool__:{json}` as an authenticated override.

### 9.2 Context model

| Signal              | Meaning                                                                                | Source                 |
| ------------------- | -------------------------------------------------------------------------------------- | ---------------------- |
| `pageContext`       | The screen the user is currently on (`patientId`, `appointmentId`, `visitId`)          | Current route          |
| `attachedContext[]` | Explicit items the user pinned in the composer (a patient, an appointment, an invoice) | Composer chips, max ~8 |

Tool argument resolution order: **explicit args in the user's message → attached context → ambient page context**. This avoids the assistant acting on the wrong patient when a user has multiple charts open across browser tabs.

### 9.3 Three-tier risk model (server-computed, never model-decided)

| Tier                          | Meaning                                                                                                            | Examples                                                                                                                                                    |
| ----------------------------- | ------------------------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Tier 0 — read**             | Always allowed if RBAC passes; never writes                                                                        | Look up a patient, list today's appointments, check a balance, search charts                                                                                |
| **Tier 1 — auto-executed**    | Runs automatically, but only for idempotent/low-blast-radius writes; surfaced to the user as a visible "done" card | Mark a thread read, revoke a not-yet-accepted staff invite, a plain forward appointment-status move with no financial/clinical impact                       |
| **Tier 2 — confirm required** | The tool returns a _proposal_; nothing is written until the user taps Confirm in the chat UI                       | Cancel an appointment, issue a prescription, create an invoice line item, send a reminder/message to a patient, edit clinical notes, change clinic settings |

Escalation rules (always override a tool's default tier):

- **Bulk escalation** — 2+ writes requested in one turn forces every one of them to Tier 2
- **Cross-scope escalation** — acting on a patient/appointment outside the current page context and outside pinned context forces Tier 2
- **External-send escalation** — anything that sends a real message to a patient (reminder, visit summary, reschedule notice) is _always_ Tier 2 and rendered with a visually distinct, destructive-styled confirm ("Send", not generic "Confirm") — matches kame-homes' `EXTERNAL_SEND_TOOL_NAMES` pattern exactly, because "the AI silently messaged a patient" is a categorically worse failure than "the AI silently updated an internal field"
- **Clinical-write escalation** — any write that touches a SOAP note, prescription, or diagnosis is _always_ Tier 2, no exceptions, regardless of how the generic classifier would otherwise score it

### 9.4 Safety model (applies to every tool, no exceptions)

1. **Independent RBAC re-check per tool call** — every tool re-derives the permission it needs and re-checks it against the original request's auth token, never trusting anything the model asserts about who's calling or what they're allowed to do. A tool call with a forged patient/appointment id fails the same way a direct API call would.
2. **Re-check immediately before execution** — even a Tier 1 auto-write re-validates against current DB state right before writing (e.g. the appointment hasn't already been cancelled by someone else in the meantime); mismatches hard-fail instead of writing.
3. **Post-generation grounding check** — every fact the assistant states (a balance, a date, a status) is checked against real tool-result data before being shown; ungrounded claims are stripped, not shown. The assistant must never invent a patient, a balance, or a chart entry.
4. **Full audit trail** — every executed write (Tier 1 auto or Tier 2 confirmed) is recorded in the same `activity_log` from §6.11, visible on the relevant patient/appointment record as "Actions taken by AI assistant."
5. **A "never build" list at the tool-catalog level** — irreversible or maximal-blast-radius actions (deleting a patient record, deleting a chart version, bulk-messaging the entire patient list) are simply never registered as callable tools. No prompt can make the model call a tool that doesn't exist.
6. **Cost control** — per-clinic daily AI usage cap (already noted in `tech-stack.md`'s AI section), enforced server-side before any model call, not just measured after the fact.

### 9.5 Representative tool catalog (MVP scope — illustrative, not exhaustive)

| Tool                             | Type  | Tier                                                              | Notes                                                                                                      |
| -------------------------------- | ----- | ----------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------- |
| `search_patients`                | read  | 0                                                                 | Name/contact/ID fuzzy search                                                                               |
| `get_patient`                    | read  | 0                                                                 | Full profile + medical info the caller's role is allowed to see                                            |
| `list_appointments`              | read  | 0                                                                 | Filterable by date/doctor/status                                                                           |
| `get_available_slots`            | read  | 0                                                                 | Real open slots for a doctor/date, respects working hours + existing bookings                              |
| `check_patient_balance`          | read  | 0                                                                 | Outstanding balance lookup                                                                                 |
| `search_charts`                  | read  | 0                                                                 | Semantic chart search (§8.3)                                                                               |
| `propose_book_appointment`       | write | 1 (routine) / 2 (if outside working hours or double-booking risk) | Books a new appointment                                                                                    |
| `propose_reschedule_appointment` | write | 1 (simple move) / 2 (same-day / short-notice)                     |                                                                                                            |
| `propose_cancel_appointment`     | write | 2 (always)                                                        |                                                                                                            |
| `draft_soap_note`                | read  | 0                                                                 | Produces a draft only — never writes a chart version (§8.2)                                                |
| `propose_save_soap_note`         | write | 2 (always)                                                        | Doctor-only; creates a new chart version                                                                   |
| `propose_issue_prescription`     | write | 2 (always)                                                        | Doctor-only; runs the allergy/interaction check (§8.6) first and surfaces any flag before the confirm card |
| `propose_create_invoice_line`    | write | 2 (always)                                                        |                                                                                                            |
| `propose_send_reminder`          | write | 2 (always) + external-send styling                                | Sends a real message to a patient                                                                          |
| `propose_generate_document`      | write | 2 (always)                                                        | Certificate/referral/lab request draft, patient must review before it's marked issued                      |

### 9.6 UI/UX

- Floating launcher, bottom-right, on every dashboard screen (hidden from patients — this is a staff/doctor tool, not patient-facing; the patient-facing assistant is the separate, more restricted §8.4 booking/FAQ assistant)
- Chat panel shows: streaming answer text, structured cards (patient card, appointment card, invoice card — kame-homes' `ChatBlock` pattern adapted to clinic entities), and confirmation cards for Tier 2 actions with Confirm/Cancel
- Quick-action suggestion chips relevant to the currently pinned context (viewing a patient → "Book follow-up", "Show last 3 visits", "Check balance")
- Full turn streams over SSE (matches `tech-stack.md`'s existing SSE choice for AI streaming) so the doctor sees progress, not a spinner
- Two-layer kill switch: platform-wide default off until stable, then clinic-level opt-in toggle in Settings (§6.12) — same safety-first rollout pattern as kame-homes shipped its own dashboard assistant with

### 9.7 What this replaces (the actual product promise)

Concretely, once this ships, a receptionist or doctor should be able to do all of the following by typing instead of navigating screens:

- "Book Maria Santos for a follow-up next Tuesday afternoon" → assistant checks availability, proposes a slot, confirms on tap
- "What's Mr. dela Cruz's balance?" → instant answer, no navigating to Billing
- "Draft a SOAP note: 34F, 3-day cough, no fever, clear lungs, prescribing amoxicillin 500mg TID x7d, follow up if no improvement in 5 days" → structured draft appears in the chart form, doctor reviews and confirms
- "Send tomorrow's patients their reminder now instead of waiting for the scheduled time" → confirm card, then sent
- "Generate a fit-to-work certificate for Juan, cleared today" → draft document, doctor confirms and it's saved to the patient's file

## 10. Non-Functional Requirements

### Security & compliance

- HTTPS everywhere; JWT access + refresh tokens (per `tech-stack.md`)
- Role-based access enforced server-side on every endpoint, never only in the UI (mirrors kame-homes' explicit lesson that "RLS/DB policy is not the access-control layer — server-side checks are")
- Patient data is PII/PHI: never logged in plaintext, never included in error tracking payloads (structured logs without PHI, per `tech-stack.md`)
- Data privacy compliance for the target market (Philippine Data Privacy Act at minimum; design fields/consent capture so HIPAA-equivalent controls are not a rewrite later)
- Digital consent capture for data storage/AI-assisted processing at patient intake (checkbox + timestamp, minimum for MVP; e-signature capture is a nice-to-have, not required for v1)
- Backups: automated daily database backup, tested restore procedure documented before pilot launch
- Object storage access only via short-lived presigned URLs, never public buckets

### Reliability & performance

- Uptime target ≥99.5% during business hours (Asia/Manila)
- Double-booking prevention enforced at the database level (exclusion constraint), not just client-side validation
- Realtime queue/status updates (WebSocket) degrade gracefully to polling if the connection drops — front desk must never be blind to patient status because of a dropped socket
- AI assistant failures must never block the underlying manual workflow — every AI action has a manual dashboard equivalent (the assistant is an accelerator, not the only path)
- Offline resilience (Phase 36): a read-only cache, not full offline write-and-sync. Today's schedule and the patient roster stay viewable (visibly marked stale) during a connectivity drop; the one write path allowed offline is a SOAP note in progress, which queues locally and syncs automatically on reconnect (single-writer assumption — not concurrent multi-device edits). Booking, billing, and prescriptions stay online-only and block with an explicit "requires connection" state rather than a silently-failed request. See `docs/architecture/offline-resilience.md`.

### Accessibility & mobile

- Every screen usable at 375px (phone) through desktop; 44×44px touch targets — front desk frequently runs on a tablet
- Keyboard navigable dashboard for desktop users
- Printable documents (Rx, certificates, invoices, SOAP notes) must render correctly on standard paper sizes, not just look right on screen

### Observability

- Error tracking (Sentry or equivalent) on both frontend and backend, PHI-scrubbed
- Structured logs for every AI tool call (tool name, tier, outcome) separate from the clinical audit log, for debugging without exposing patient content

## 11. Data Model Additions

New tables needed beyond the `tech-stack.md` "Core tables (v1)" list, to support §6.6–§6.12 and §9:

| Table                                                 | Purpose                                                                                          |
| ----------------------------------------------------- | ------------------------------------------------------------------------------------------------ |
| `prescriptions`                                       | Header + line items (drug, dosage, frequency, duration) per visit                                |
| `invoices`, `invoice_line_items`                      | Billing per visit; payment records                                                               |
| `payments`                                            | Payment method, amount, date, reference; linked to an invoice                                    |
| `documents_generated`                                 | Certificates/referrals/lab requests issued, with template used and final content snapshot        |
| `reminders`                                           | Scheduled and sent reminder log (channel, status, linked appointment)                            |
| `patient_recalls`                                     | Follow-up/recall schedule derived from SOAP follow-up dates and chronic-condition rules          |
| `ai_assistant_conversations`, `ai_assistant_messages` | Chat history for the AI Clinic Assistant, scoped per clinic/user                                 |
| `ai_assistant_actions`                                | Every Tier 1/Tier 2 action the assistant executed, feeding the shared `activity_log`             |
| `document_templates`                                  | Clinic-editable templates for certificates/referrals/lab requests                                |
| `soap_note_versions`                                  | Explicit versioning if not already covered by `soap_notes` being append-only per `tech-stack.md` |

`activity_log` (already in `tech-stack.md`) becomes the shared audit surface for both manual dashboard actions and AI assistant actions — one table, one place to review "what happened and who/what did it."

## 12. Production Readiness Checklist

MVP is not "done" until every item below is true, not just "the feature exists in a demo":

**Core functionality**

- [ ] A brand-new clinic can complete onboarding (§6.1) with zero engineering support — Playwright `e2e/onboarding.spec.ts` + `completeOnboarding` helper green; uninstructed pilot sign-off still required
- [x] A full patient lifecycle works end-to-end: book → arrive → consult (SOAP + Rx) → bill → pay (`apps/api/tests/test_patient_lifecycle.py`; reminder cron covered separately in `test_reminders.py`)
- [x] Double-booking is impossible even under concurrent requests (`test_concurrent_double_booking`, `test_public_staff_booking_race`, `scripts/load/concurrent_booking.py`)
- [ ] Every printable document (Rx, certificate, invoice, SOAP note) renders correctly on real paper, not just on screen — PDF endpoints tested; physical print is a manual gate

**Data safety**

- [ ] Automated backups running and a restore has been tested at least once against a real snapshot — `pnpm run backup:db:dev` works via host `pg_dump` or Docker Compose fallback; prod Neon drill requires `deskwave`
- [x] Chart versioning confirmed — no code path can overwrite a saved SOAP note in place (`test_soap.py`, `test_soap_versions_are_immutable`)
- [x] RBAC verified: `reception` cannot read `clinical_notes` / SOAP when clinic has not opted in (`test_security_rbac.py`, `test_soap.py`)

**AI assistant**

- [x] Every Tier 2 action requires explicit confirm in tests (`test_assistant.py`: cancel + SOAP save)
- [x] Assistant failures (timeout, model error) never leave a half-applied write — Tier 1 tool errors roll back (`test_tier1_tool_error_emits_sse_error_no_write`); Tier 2 confirm failures leave state unchanged (`test_confirm_failure_leaves_state_unchanged`); live LLM timeout adversarial suite still manual
- [x] Per-clinic AI usage cap enforced (`test_soap_draft.py::test_soap_draft_usage_cap_blocks`)
- [x] Kill switch verified (`test_assistant.py`: platform + clinic toggle)

**Compliance & trust**

- [x] Consent capture live at patient intake (`data_processing_consent_at`, `PatientNewPage` checkbox, `test_security_rbac.py`)
- [ ] No PHI present in logs or error-tracking payloads — conventions in `phi-data-safety.mdc`; prod Sentry spot-check before pilot
- [x] Audit log (`activity_log`) on service-layer mutations including assistant confirms, billing confirm, cron purges

**Operational readiness**

- [ ] Uptime monitoring and alerting configured before the first pilot clinic goes live
- [x] Support channel defined (`docs/architecture/deployment.md` § Monitoring & incident response)
- [x] Written rollback/incident plan (`docs/architecture/deployment.md` § Monitoring & incident response + restore runbook)

## 13. Build Order / Phasing

Extends `tech-stack.md`'s existing build order with the modules and AI features this doc adds. Each phase should ship with `type-check`/`lint`/tests green and the relevant checklist items from §12 satisfied before moving on.

1. Monorepo scaffold, Docker Compose, auth, roles (§6.1, §6.11)
2. Clinic onboarding wizard (§6.1) + multi-doctor support (§7.1)
3. Patients (§6.3) + appointments + exclusion constraint (§6.4)
4. Day calendar + drag reschedule + public self-service booking link (§7.3)
5. Status board + WebSockets (live waiting-room queue, §6.4/§6.2)
6. Walk-in, reschedule, no-show, recurring series (rrule + ARQ expand)
7. SOAP versions + vitals + follow-up + specialty templates (§6.5, §7.8, §7.9)
8. Prescriptions module (§6.6)
9. Billing & payments (§6.7)
10. Document generation (§6.8)
11. Reminders + recall campaigns (§6.9, §7.6, §7.7)
12. Reports & analytics (§6.10)
13. Audit log surfaced in UI (§6.11) — backend logging should exist from phase 1 onward, this phase is the visible review UI
14. PydanticAI SOAP draft + SSE streaming (§8.2)
15. Transcription + pgvector chart search (§8.2, §8.3)
16. **AI Clinic Assistant v1** (§9) — read-only tools first (Tier 0), then Tier 1 auto-writes, then Tier 2 confirm-required writes, following the same staged rollout kame-homes used for its own assistant
17. AI safety checks on prescriptions (§8.6), AI billing/receipt assist (§8.7)
18. Patient-facing booking/FAQ text assistant (§8.4), AI visit summaries (§8.5)
19. Hardening pass: no-show prediction (§8.8), command palette (§8.9), full production readiness checklist (§12) sign-off

## 14. Out of Scope for MVP (Phase 2+)

Explicitly deferred, with the reasoning for deferral so it isn't re-litigated mid-build:

| Deferred                                                                                    | Why it's real but not MVP                                                                                                                                                                                                                                                                                                              |
| ------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Live voice AI receptionist (speech-to-speech phone/web calls)                               | Needs its own real-time audio pipeline, per-minute cost caps, and a multi-phase latency/safety hardening pass — kame-homes' own build of this took six sub-phases after v1 shipped. Ship the text assistant first, prove the grounding/safety pattern, then revisit.                                                                   |
| Telemedicine video consults                                                                 | Different infrastructure (video/WebRTC), different compliance surface; not needed for a clinic replacing paper with a dashboard                                                                                                                                                                                                        |
| Consolidated cross-clinic reporting / franchise dashboard (patient content across branches) | Org envelope + per-clinic enrollment ships in Phase 41; aggregate-only org metrics remain. Full franchise analytics deferred. Re-confirmed explicitly deferred in Phase 38 (§6.15) — the target segment is still solo/small clinic, not chains, so multi-branch reporting is not built even as the rest of that phase's backlog ships. |
| Insurance EDI / live claims submission to HMOs                                              | Requires per-insurer integration work; MVP tracks claims as structured notes (§6.7) which is sufficient for a small clinic's actual workflow today                                                                                                                                                                                     |
| Inventory management (medicine stock, consumables)                                          | Only relevant to clinics that dispense on-site at scale; not a blocker for the primary target users                                                                                                                                                                                                                                    |
| AI differential-diagnosis suggestions                                                       | Legally sensitive; MVP AI stays scoped to drafting/search/flagging, never diagnosis                                                                                                                                                                                                                                                    |
| Wearable / remote patient monitoring integration                                            | No signal yet that target users need this before the core platform is solid                                                                                                                                                                                                                                                            |
| Native mobile apps (iOS/Android)                                                            | PWA (§8.9) covers the "works well on a tablet/phone" need without a second codebase                                                                                                                                                                                                                                                    |

## 15. Open Questions & Decisions Needed

Track and resolve before or during the relevant build phase — do not silently assume an answer:

1. **Target market for compliance defaults** — confirm Philippines-first (BIR receipt numbering, PH Data Privacy Act, GCash as a payment method) vs. designing compliance fields to be market-agnostic from day one.
2. **Medicine dispensing on-site** — do any pilot clinics sell medicine directly (pharmacy-in-clinic)? If yes, billing (§6.7) needs an inventory-lite line item type sooner than Phase 2.
3. **SMS provider cost ownership** — clinic pays per-SMS (opt-in, metered, per `tech-stack.md`) vs. bundled into a subscription tier — needs a pricing-model decision before §6.9 ships to real clinics.
4. **AI usage cost ownership** — same question as SMS: per-clinic daily cap is decided (§9.4), but who absorbs the LLM cost (platform subscription vs. usage-based add-on) is a business decision, not just a technical cap.
5. **E-signature requirement** — is a typed/uploaded signature image sufficient for prescriptions and certificates in the target market, or is a legally-binding e-signature (timestamped, tamper-evident) required? Affects §6.6/§6.8 scope.
6. **Reception's default clinical-notes visibility** — §6.11 defaults reception to no access with an opt-in override; confirm this matches what pilot clinics actually expect before locking the permission matrix.
7. **Pilot clinic selection** — who are the first 2–3 pilot clinics, and do any of them have an existing patient dataset that needs import/migration tooling (not currently scoped in §6–§9)?
