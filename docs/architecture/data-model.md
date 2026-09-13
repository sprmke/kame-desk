# Data model

Standing entity reference for DoctorDesk. Tables are grouped by the phase that introduces them (see `docs/phases/README.md`). This doc is updated as each phase ships — treat "Status" as the truth, not an assumption from the phase file alone.

## Conventions that apply to every table

- Every clinic-scoped table carries `clinic_id` (FK to `clinics`). No query anywhere trusts a client-supplied `clinic_id` — it is always derived from the authenticated user's `clinic_memberships` row for the request's active clinic.
- Money fields are `Decimal`/integer-cents, never `float` — introduced in Phase 9, applies to every monetary field added afterward.
- Timestamps are stored UTC; all patient-facing display is converted to `Asia/Manila` at the edge.
- Append-only tables (`activity_log`, `soap_notes`, `visit_status_events`, `soap_note_embeddings`, `ai_assistant_actions`) never have an `UPDATE`/`DELETE` code path targeting their core content — new state is always a new row.
- Alembic migrations are additive only; a shipped migration under `apps/api/migrations/versions/` is never edited.

## Entity map by phase

| Phase | Tables introduced                                                                                                                                                                                    | Status                 |
| ----- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------- |
| 1     | `clinics`, `users`, `clinic_memberships`, `refresh_tokens`, `activity_log`                                                                                                                           | **Shipped** (Phase 1)  |
| 2     | `doctor_profiles`, `service_fees`, `staff_invitations` (+ `clinics` extended: `working_hours`, `holiday_dates`, license/accreditation, onboarding flags)                                             | **Shipped** (Phase 2)  |
| 3     | `patients`, `patient_medical_info`, `patient_vitals`, `patient_files`, `rooms`, `appointments` (+ exclusion constraint)                                                                              | **Shipped** (Phase 3)  |
| 4     | `appointments.booking_source` (column), `clinics.slug`, `clinics.public_booking_auto_confirm`                                                                                                        | **Shipped** (Phase 4)  |
| 5     | `visit_status_events`, `appointments.current_visit_status` (column)                                                                                                                                  | **Shipped** (Phase 5)  |
| 6     | `appointment_series`, `appointments.series_id`/`series_occurrence_index`, `patients.no_show_count`                                                                                                   | **Shipped** (Phase 6)  |
| 7     | `soap_notes` (versioned), `document_templates` (SOAP-scoped), `clinics.reception_can_view_soap`                                                                                                      | **Shipped** (Phase 7)  |
| 8     | `prescriptions`, `prescription_items`, `drug_reference` (seeded)                                                                                                                                     | **Shipped** (Phase 8)  |
| 9     | `invoices`, `invoice_line_items`, `payments`, `clinics.receipt_numbering_config` (column)                                                                                                            | **Shipped** (Phase 9)  |
| 10    | `documents_generated` (+ `document_templates` extended: `body_template`, `is_active`)                                                                                                                | **Shipped** (Phase 10) |
| 11    | `reminders`, `patient_recalls`, `clinics.notification_preferences`/`twilio_credentials_encrypted` (columns)                                                                                          | **Shipped** (Phase 11) |
| 12    | none (derived/aggregated queries only)                                                                                                                                                               | **Shipped** (Phase 12) |
| 13    | none (indexes only on `activity_log`)                                                                                                                                                                | **Shipped** (Phase 13) |
| 14    | `clinic_ai_usage`                                                                                                                                                                                    | **Shipped** (Phase 14) |
| 15    | `soap_note_embeddings`, `consultation_recordings`                                                                                                                                                    | **Shipped** (Phase 15) |
| 16    | `ai_assistant_conversations`, `ai_assistant_messages`, `ai_assistant_actions`; `clinics.ai_assistant_enabled`                                                                                        | **Shipped** (Phase 16) |
| 17    | `billing_extraction_attempts`                                                                                                                                                                        | **Shipped** (Phase 17) |
| 18    | `visit_summaries`, `patient_assistant_conversations`                                                                                                                                                 | **Shipped** (Phase 18) |
| 19    | none (no-show risk is computed on read)                                                                                                                                                              | **Shipped** (Phase 19) |
| 20    | `visit_summaries.generation_failed` (column)                                                                                                                                                         | **Shipped** (Phase 20) |
| 21    | `account_tokens`; `users.email_verified_at`; `clinics.deletion_requested_at`                                                                                                                         | **Shipped** (Phase 21) |
| 22    | none (receipt numbering API over existing `clinics.receipt_numbering_config`)                                                                                                                        | **Shipped** (Phase 22) |
| 23    | none (merge/import over existing `patients` + related FKs)                                                                                                                                           | **Shipped** (Phase 23) |
| 24    | `appointment_waitlist`; `service_fees.duration_minutes`; `appointments.service_fee_id`                                                                                                               | **Shipped** (Phase 24) |
| 25    | `clinical_orders`; expanded `drug_reference` seed; `documents_generated.referral_*`                                                                                                                  | **Shipped** (Phase 25) |
| 26    | `credit_notes`; `insurance_claims`                                                                                                                                                                   | **Shipped** (Phase 26) |
| 27    | `patients.reminders_opted_out`                                                                                                                                                                       | **Shipped** (Phase 27) |
| 28    | none (report `doctor_name` + UI filters)                                                                                                                                                             | **Shipped** (Phase 28) |
| 29    | `clinics.assistant_disabled_tools`                                                                                                                                                                   | **Shipped** (Phase 29) |
| 30    | `clinics.status`; `clinics.plan_key`; `platform_feature_flags`; `platform_audit_log`                                                                                                                 | **Shipped** (Phase 30) |
| 31    | none                                                                                                                                                                                                 | **Shipped** (Phase 31) |
| 32    | none                                                                                                                                                                                                 | **Shipped** (Phase 32) |
| 33    | `payers`, `eligibility_checks`, `loa_requests`; `insurance_claims.payer_type`/`loa_request_id`                                                                                                       | **Shipped** (Phase 33) |
| 34    | `clinics.bir_compliance_config` (column)                                                                                                                                                             | **Shipped** (Phase 34) |
| 35    | `clinics.whatsapp_enabled`/`whatsapp_phone_number_id`/`whatsapp_credentials_encrypted` (columns); `reminders.channel` gains `whatsapp`                                                               | **Shipped** (Phase 35) |
| 36    | `soap_notes.client_draft_token` (column)                                                                                                                                                             | **Shipped** (Phase 36) |
| 37    | `patient_portal_tokens`                                                                                                                                                                              | **Shipped** (Phase 37) |
| 38    | `membership_plans`, `patient_memberships`, `patient_survey_responses`; `clinics.growth_settings`; `invoices.financing_status`; `generated_documents.chart_share_token_hash`/`chart_share_expires_at` | **Shipped** (Phase 38) |
| 39    | `tooth_chart_entries`                                                                                                                                                                                | **Shipped** (Phase 39) |
| 41    | `organizations`, `organization_subscriptions`, `organization_enrolled_clinics`, `clinics.organization_id`                                                                                            | **Shipped** (Phase 41) |

## Core tenancy model

```
users ──< clinic_memberships >── clinics >── organizations
         │                         │              │
         │                         │              └── organization_subscriptions
         │                         └── organization_enrolled_clinics
         └── (organizations.owner_id)
```

Operational/PHI data stays under `clinics`. Billing, plan, and multi-clinic ownership live on `organizations`:

```
users ──< clinic_memberships >── clinics
                                    │
                                    ├──< doctor_profiles (user_id + clinic_id)
                                    ├──< patients
                                    ├──< appointments >── patients
                                    │                  └── doctor_profiles
                                    ├──< soap_notes (versioned, per appointment)
                                    ├──< prescriptions >── patients
                                    ├──< invoices >── patients
                                    └──< activity_log (append-only)
```

A `user` can belong to more than one `clinic` (multiple `clinic_memberships` rows), each with an independent `role`. A `clinic` can have 2+ `doctor_profiles`. An `organization` can have multiple `clinics` via `organization_enrolled_clinics` (enrollment status: `pending_enrollment`, `active`, `deactivated`). Plan and doctor seat limits pool at the org level. **Strict PHI isolation:** no shared patient registry across clinics in one org; org surfaces show aggregates only.

Signup creates `organization` + `organization_subscription` + first `clinic` + `organization_enrolled_clinic` (active) + `clinic_memberships` (owner). Additional clinics are created by the org owner; enrollment starts `pending_enrollment` until Super Admin activates (manual billing rail).

## Load-bearing invariants (do not weaken these in a later phase without updating this doc and the PRD)

1. **Double-booking prevention is a DB-level guarantee.** `appointments` carries a `btree_gist` exclusion constraint on `(doctor_id, tsrange(scheduled_start, scheduled_end))` (and separately on `room_id` when assigned), filtered to non-terminal appointment statuses. This is not app-level validation — it holds under concurrent writes. See `docs/phases/phase-03-patients-appointments.md`.
2. **SOAP notes are never overwritten in place.** Every save is a new row with an incremented `version_number`; the "current" note is the max version for an appointment. See `docs/phases/phase-07-soap-vitals-templates.md`.
3. **`activity_log` is append-only** and covers every mutating action, including AI-assistant-executed writes (`actor_type = 'ai_assistant'`). No code path updates or deletes a row.
4. **Prescriptions and issued documents are immutable once issued.** Voiding is a status change, never a delete; a `final_content_snapshot` on generated documents freezes content even if the source template later changes.
5. **Allergy/medication data is structured, not free text** (`patient_medical_info`), specifically so Phase 8's deterministic safety check and Phase 17's AI explanation layer have real data to operate on.
6. **Every table that isn't global carries `clinic_id`.** There is no cross-clinic query anywhere in the product.

## Phase 3 specifics (patients + appointments)

### Patient search (`pg_trgm`)

Fuzzy patient search uses the `pg_trgm` extension with `similarity()` on `full_name` and `ilike` fallbacks on `contact_number` / `patient_number` text. All queries are filtered by `clinic_id` from the authenticated membership — never from the client.

### Double-booking exclusion constraints

Migration `003_patients_appointments.py` adds two `EXCLUDE USING gist` constraints on `appointments`:

- **Doctor:** `(doctor_id WITH =, tstzrange(scheduled_start, scheduled_end, '[)') WITH &&)` where `appointment_status NOT IN ('Cancelled', 'No Show', 'Rescheduled')`
- **Room:** same shape on `room_id` when `room_id IS NOT NULL`

`scheduled_start` / `scheduled_end` are `TIMESTAMPTZ` (UTC in DB). App validates working hours in `Asia/Manila` before insert; the exclusion constraint is the concurrency-safe backstop. API returns **409** with a clean message when Postgres raises `ExclusionViolation`.

### Medical info shape

`patient_medical_info` is a separate table (1:1 with `patients`). Allergies are a structured JSON array (`substance`, `reaction`, `severity`). `allergies_reviewed: bool` distinguishes "none known" from "not yet asked".

### Recurring series (Phase 6)

- `appointment_series`: `rrule_string`, `series_start`, optional `series_end`, `duration_minutes`, patient/doctor/clinic FKs.
- Each occurrence is a normal `appointments` row with `series_id` + `series_occurrence_index` (unique together).
- Expansion window: 90 days from `series_start`; conflicts returned to the client, not silently dropped.
- `patients.no_show_count` incremented when `POST .../mark-no-show` runs (for Phase 19 prediction).

### SOAP versioning (Phase 7)

- `soap_notes`: one row per save; unique `(appointment_id, version_number)`. Clinical fields are never updated via API — only `signed_at` / `signature_image_url` may be set on sign. `client_draft_token` (Phase 36): optional, unique per `appointment_id` (Postgres allows multiple NULLs, so normal online saves are unaffected); when set, a retried `POST .../soap-notes` with the same token returns the already-saved row instead of inserting a duplicate — makes a queued offline draft's flush safe to retry. See `docs/architecture/offline-resilience.md`.
- `document_templates`: clinic-scoped or global SOAP template bodies (Phase 10 extends for other document types).
- `clinics.reception_can_view_soap`: default `false`; when `true`, reception may read SOAP history but never write.
- `patient_vitals.visit_id` links vitals to a visit when recorded from the SOAP flow (optional).

### Prescriptions (Phase 8)

- `prescriptions`: `draft` → `issued` → `voided`; PDF stored in R2 on issue; `override_reason` and `conflict_flags` captured when safety checks are bypassed.
- `prescription_items`: line items; editable only while draft.
- `drug_reference`: curated open list (expanded in Phase 25). Drugs outside the list return an explicit `unchecked` flag. Not a national pharmacology database.
- `clinical_orders`: lab/imaging lifecycle (`ordered` → `in_progress` → `resulted` / `cancelled`) with optional result text.
- `documents_generated.referral_recipient` / `referral_status` / `referral_outcome`: referral tracking besides the PDF.
- `credit_notes`: refund or adjustment against a paid invoice. Does not void the original OR.
- `insurance_claims`: clinic-tracked HMO claim status; `payer_type` (`hmo`/`philhealth`/`self_pay`/`other`), optional `loa_request_id` (Phase 33).

### PH payer workflow (Phase 33)

- `payers`: clinic-managed directory of HMO/PhilHealth names (`payer_type`, `is_active`) reused by claim/eligibility/LOA forms.
- `eligibility_checks`: structured HMO/PhilHealth coverage checks — `payer_name`, `payer_type`, `member_id`, `status` (`pending`/`verified`/`denied`/`expired`), `verified_amount`. History is additive (no overwrite); latest per patient/payer drives the `check_eligibility_status` assistant tool. No live insurer call in MVP — status is staff-entered behind the `claims_partner` adapter (`app/services/claims_partner.py`).
- `loa_requests`: `requested` → `submitted` → `approved`/`denied`; optional link to an `insurance_claims` row; `document_object_key` for the uploaded LOA document (R2). `submitted_at`/`decided_at` set automatically on the matching status transition.

### Billing (Phase 9)

- `invoices`: `draft` → `issued` → `partially_paid` / `paid` / `void`; sequential `invoice_number` per clinic; optional `appointment_id`.
- `invoice_line_items`: editable in draft only; `amount = quantity × unit_price` (`Decimal`).
- `payments`: append-only; partial payments supported; void blocked when payments exist.
- `clinics.receipt_numbering_config`: JSON `{ prefix, next_number, pad_width }`; incremented under row lock on issue.

### BIR compliance depth (Phase 34)

- `clinics.bir_compliance_config`: JSON `{ tin, registered_name, registered_address, vat_registered, compliance_mode, accreditation_number, accreditation_valid_until }`. `compliance_mode` is one of `not_yet_accredited` / `ptu` / `cas`. `registered_name`/`registered_address` fall back to `clinics.name`/`clinics.address` on the receipt PDF when unset. Embedded on `ClinicRead.bir_compliance` (readable by any clinic staff, same visibility as `receipt_numbering`); edits are `OwnerAdmin`-gated via `GET`/`PUT /clinics/{id}/bir-compliance`. Never blocks invoice issuance — an incomplete or expired config only surfaces a non-blocking banner on the Billing page.

### Generated documents (Phase 10)

- `document_templates`: extended with `body_template` (HTML from the WYSIWYG editor, with `{{patient.full_name}}` tokens) and `is_active` for letter types; SOAP templates keep JSON `body`. Issued PDFs honor basic HTML (headings, lists, bold/italic). Plain-text bodies still render.
- `documents_generated`: draft → issued; `final_content_snapshot` immutable; PDF stored in R2; linked `patient_files` row on issue.

### Reminders and recalls (Phase 11)

- `reminders`: per-appointment notification rows (`confirmation`, `reminder_24h`, `reminder_2h`, `reschedule_notice`, `cancellation_notice`); channels `email` / `sms` / `whatsapp` (Phase 35); status `pending` → `sent` / `failed` / `cancelled`; unique `reply_token` used both by the public respond link and (for WhatsApp) as the quick-reply button payload.
- `patient_recalls`: follow-up and chronic-condition recall queue; unique `(clinic_id, patient_id, source, due_date)` for idempotent generation.
- `clinics.notification_preferences`: JSONB toggles and chronic rules; `twilio_credentials_encrypted`: Fernet blob (never plain API keys in JSONB).

### Staff in-app notifications (Phase 40)

- `notifications`: clinic-scoped alert rows (`type` CHECK catalog), `title`, optional `body`, `href`, `metadata`, `dedupe_key`, `audience_roles`, optional `target_user_id` / `target_doctor_id`, optional `actor_user_id`. Partial unique on `(clinic_id, type, dedupe_key)` when dedupe set.
- `notification_reads`: per-user read tracking; absence of a row means unread.
- `clinic_memberships.in_app_notification_prefs`: optional JSONB per-type `{ in_app, push }` toggles.
- `push_subscriptions`: Web Push endpoints per user/clinic when VAPID is configured.
- Realtime: Redis pub/sub → `/ws/clinic/{id}` events `notification.created` / `notification.updated`.
- Distinct from `clinics.notification_preferences` (patient reminder channel prefs, Phase 11).

### Messaging channels (Phase 35)

- `clinics.whatsapp_enabled`: bool preference toggle (mirrors `sms_enabled`).
- `clinics.whatsapp_phone_number_id`: plain, **unique-indexed** string — Meta's phone number identifier, not a secret; used to route inbound webhook traffic to the owning clinic (`GET/POST /webhooks/whatsapp`).
- `clinics.whatsapp_credentials_encrypted`: Fernet blob holding `{"access_token": ...}`, same `secrets_crypto` pattern as Twilio. `PATCH /clinics/{id}/notification-preferences` rejects a `whatsapp_phone_number_id` already claimed by another clinic (400).
- Full adapter pattern: `docs/architecture/messaging-channels.md`.

### Patient portal (Phase 37)

- `patient_portal_tokens`: `patient_id` + `clinic_id` (both indexed), `purpose` (`"login"`), hashed `token_hash` (unique), `delivery_channel` (`email`/`sms`), `expires_at` (15 min TTL), `used_at` (single-use). Modeled on `account_tokens` (Phase 21), not on `reminders.reply_token` — PHI access needs the stronger expiring/single-use guarantee.
- No new patient-identity table: a `patient_access` JWT (`sub` = patient id, `clinic_id` claim, 30 min) is the session — see `docs/architecture/security-compliance.md` § Patient portal auth tier.
- Reuses existing tables read-only: `appointments` (visit history), `soap_notes` (diagnoses, gated on `signed_at IS NOT NULL`), `patient_vitals` (vitals trend), `invoices`/`payments` (balance), `patient_files` (documents, downloaded via the same `storage_service.create_presigned_download` staff use).

### Growth & retention (Phase 38)

- `membership_plans`: `clinic_id`, `name`, `price`, `billing_interval` (`monthly`/`quarterly`/`annual`), `included_services` (JSONB list of `{category, count_per_period}` allowances), `is_active`.
- `patient_memberships`: `clinic_id`, `patient_id`, `plan_id`, `status` (`active`/`cancelled`/`expired`), `started_at`, `current_period_end`, `usage_this_period` (JSONB `{category: count}`, reset lazily on period rollover when the membership is read), `cancelled_at`.
- `patient_survey_responses`: `clinic_id`, `patient_id`, `visit_id`, unique `reply_token`, `score` (0-10), `comment`, `sent_at`, `responded_at` (single-use — set once, replay returns 400). Same low-stakes token pattern as `reminders.reply_token`, not the stronger `account_tokens`/`patient_portal_tokens` pattern, since this carries an NPS score, not PHI.
- `clinics.growth_settings` (JSONB column, mirrors `bir_compliance_config`'s shape): `google_review_link`, `review_requests_enabled`, `doh_accreditation_number`, `doh_accreditation_valid_until`. The DOH fields are display-only trust-signal metadata — no accreditation workflow, no live DOH system connection.
- `invoices.financing_status` (nullable string column): set by the pluggable `FinancingPartner` adapter (`app/services/financing_partner.py`); `NoopFinancingPartner` is the default (feature hidden behind `settings.financing_partner_enabled`, off by default — no confirmed PH healthcare BNPL partner exists).
- `generated_documents.chart_share_token_hash` (unique) / `.chart_share_expires_at`: a scoped, expiring (7-day) share link for a referral letter's chart-summary snapshot, hashed the same way as `patient_portal_tokens.token_hash`. Resolving the public link reuses `patient_portal_service.get_chart_summary()` read-only.
- **FHIR export capability flag** (§4.2 #10): `GET /patients/{id}/fhir-export` builds a self-contained FHIR R4 `Bundle` (`Patient` + `Encounter` resources only) on demand from existing `patients`/`appointments` rows — no new table, no stored export, no live PHIE (Philippine Health Information Exchange) connection. RBAC-gated identically to chart access (`assert_soap_read`). This is intentionally a read-only, on-demand capability, not an integration — there is no PHIE sandbox/credentials to integrate against yet.
- Membership waiver never mutates an existing invoice line's price: `maybe_apply_membership_waiver` inserts an additional negative discount line ("Membership benefit (\<plan name\>)") alongside the original, preserving an audit trail of charged-vs-waived (same append-only spirit as SOAP versioning / `activity_log`).

### Dental odontogram (Phase 39)

- `tooth_chart_entries`: `clinic_id`, `patient_id`, `appointment_id` (nullable), `soap_note_id` (nullable), `tooth_number` (FDI two-digit notation, adult permanent dentition only — quadrants 1-4, teeth 1-8; primary/deciduous dentition and periodontal charting are explicitly out of scope), `surface` (nullable — mesial/distal/occlusal/buccal/lingual/incisal; null means "whole tooth"), `condition` (sound/caries/filled/missing/crown/root_canal/extraction_planned/impacted/fractured), `status` (existing/planned/completed), `procedure_code` (nullable), `invoice_line_item_id` (nullable FK, set once a `planned` entry is pushed to an invoice), `noted_at`, `created_by_user_id`.
- Append-only, same discipline as `soap_notes`: a new finding for a tooth/surface is always a new row, never an UPDATE to a prior one — this is what makes progression (caries → filled → crown) reconstructable from `noted_at` order. The odontogram UI derives "current state" per tooth by taking the latest `noted_at` row for that tooth.
- `appointment_id` and `soap_note_id` are both nullable by design (a deliberate deviation from the phase plan's literal field list, documented here): charting happens live during a visit, often before the SOAP note's first save, and the chart itself is patient-level running history, not a per-visit snapshot — the same reasoning that keeps `patient_vitals` and `clinical_orders` independent of `soap_note_id`.
- Turning a `planned` entry into an invoice line (`POST /patients/{id}/tooth-chart/{entry_id}/add-to-invoice`) reuses an existing draft invoice for the same appointment if one exists, otherwise creates one; the entry's `status` becomes `completed` and `invoice_line_item_id` is set so it can't be added twice. The draft-reuse lookup only runs when an `appointment_id` is actually known (from the request or the entry itself) — an entry charted with no appointment context always gets its own new draft rather than risking a match against an unrelated older draft invoice for the same patient.
- `invoice_line_item_id`'s FK is `ON DELETE SET NULL` (migration `040_tooth_chart_fk_ondelete`), and `invoice_service.delete_line_item` explicitly reverts any tooth chart entry pointing at a deleted line item back to `status="planned"` — deleting a mistaken invoice line never leaves a chart entry stuck `completed` with a dangling reference, and the procedure reappears on the treatment plan so it can be re-billed.
- RBAC mirrors SOAP: read via `assert_soap_read` (owner/admin/doctor, reception opt-in), write via `assert_clinical_notes_write` (owner/doctor) — write does not additionally require the writing doctor to own the appointment, since the chart is shared clinic-wide patient state.
- `activity_log`: `tooth_chart.updated` on every create and on every add-to-invoice.
- Indexing: a single composite `(patient_id, noted_at DESC)` index (`ix_tooth_chart_entries_patient_id_noted_at`) serves the per-patient history list query directly, instead of a standalone `patient_id` index plus a separate sort.
- `add_entry_to_invoice` locks the entry row (`SELECT ... FOR UPDATE`) before checking `status == "planned"`, so two concurrent requests for the same entry can't both pass the check and double-bill the same procedure.

### AI usage (Phase 14)

- `clinic_ai_usage`: per-clinic daily counters (`request_count`, `token_count`); unique `(clinic_id, usage_date)`. Checked before SOAP draft SSE; incremented after a successful stream.

### Transcription and chart search (Phase 15)

- `consultation_recordings`: audio object key in R2, `transcription_status` (`pending` / `processing` / `done` / `failed`), optional `transcript_text`.
- `soap_note_embeddings`: pgvector column (`vector(256)`), `embedding_model_version` for re-embed jobs after model upgrades.
- `clinics.recording_consent_enabled`: owner opt-in before any recording upload is accepted.

## AI Clinic Assistant (Phase 16)

- `ai_assistant_conversations`: per user/clinic chat threads.
- `ai_assistant_messages`: user/assistant turns (`role`, `content`, optional `metadata` JSON).
- `ai_assistant_actions`: Tier 2 proposals (`status` pending/confirmed/cancelled, `proposal`/`result` JSON, `external_send` flag).
- `clinics.ai_assistant_enabled`: per-clinic opt-in (Settings → Assistant).
- Platform kill switch: `PLATFORM_AI_ASSISTANT_ENABLED` env on API (default `false`). A `platform_feature_flags` row for `ai_assistant` overrides the env when present. Super Admin emails: `PLATFORM_ADMIN_EMAILS`.

Column-level detail lives in each phase file's "Database" task list (`docs/phases/phase-0N-*.md`) at the point each table is introduced — this doc intentionally stays at the entity/invariant level so it doesn't drift out of sync with the Alembic migrations that are the actual source of truth for exact columns/types. When a migration changes a table's shape from what a phase file originally specified, update the phase file's Database section in the same change.
