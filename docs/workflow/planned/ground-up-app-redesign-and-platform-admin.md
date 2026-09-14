# Ground-up app redesign + platform (Super Admin) layer

**Status:** Done (Phases 20–32 shipped in repo. `mvp.md` §12 operational gates remain open.)
**Prepared:** 2026-09-11
**Trigger:** Product owner assessment that DoctorDesk, despite all 19 MVP phases marked "Done" in `docs/phases/README.md`, is confusing, not usable by real clinics, and missing significant functionality for both clinic users and platform operators.
**Method:** Full-repo audit across 6 functional clusters (code + docs cross-referenced, not just spec review), summarized below, then translated into a phased rebuild plan.

> This plan does not replace `docs/mvp.md` — it supersedes it where findings below contradict it, and extends it where a real clinic/SaaS business needs things `mvp.md` never scoped (the platform/Super Admin layer). Once phases in this plan start shipping, fold approved scope back into `docs/mvp.md` and `docs/phases/` in the same change, per `CLAUDE.md` § Docs are the source of truth.

---

## 0. Why "all phases Done" isn't the same as "production ready"

The phase-by-phase build (`docs/phases/00`–`19`) shipped every module the original PRD asked for, but a systematic audit (see §1) found that several flagship features are **non-functional in production despite passing tests**, several data fields are **collected but never editable**, and an entire tier of the product — **running DoctorDesk as a SaaS business** — was never scoped at all. Concretely, the three most damaging findings:

1. **The AI Clinic Assistant — the product's flagship differentiator (`mvp.md` §9) — does not understand natural language in production.** It only recognizes a literal `__tool__:{"name":...}` JSON string that test code sends directly. A real user typing "book Maria Santos Tuesday afternoon" gets a canned reply. The patient-facing booking assistant is gated behind a test-only env flag for its write tools. This is not a rough edge — the feature does not do the thing it's named for outside of tests.
2. **SMS reminders are a stub that logs and pretends to succeed** while Settings presents a full, working-looking Twilio credentials form. Staff will configure it, believe reminders are going out, and only find out otherwise when a patient no-shows.
3. **There is no layer above "one clinic" anywhere in the product** — no Super Admin, no plan/subscription model, no way to suspend a tenant, no cross-clinic visibility, no pricing page. `Clinic` doesn't even have a `status` column. You cannot run this as a multi-tenant business today; you can only run one clinic's install of it.

Beyond those three, every module has a mix of critical gaps (data collected with no way to edit it, workflows that dead-end, silent failures) and usability debt (raw UUIDs shown to users, unfiltered technical audit logs, flat unstructured navigation to some modules). Full findings are in §1; they are the basis for every phase in §4.

---

## 1. Audit findings by cluster (verified against code, not just docs)

Severity: 🔴 Critical (blocks real clinic go-live) · 🟡 Important (usability/trust debt) · ⚪ Nice-to-have.

### 1.1 Identity, Onboarding, Multi-doctor, Team, Settings, RBAC

- 🔴 No password reset / forgot-password flow at all (`auth.py` has no reset endpoints; `LoginPage.tsx` has no link). A locked-out owner has no recovery path.
- 🔴 No email verification — tokens are issued immediately on registration to an unverified address.
- 🔴 No data export or account/data-deletion path, despite `mvp.md` §6.12 and the Philippine Data Privacy Act target requiring it.
- 🔴 Certificates/referrals skip the PRC-license/signature completeness gate that prescriptions enforce (`document_service.py` defaults to a blank license instead of blocking) — legally-facing documents can go out incomplete with no warning.
- 🟡 Working hours, holidays, and clinic branding are editable only during onboarding — no post-onboarding "Clinic" settings page exists, even though the API supports it.
- 🟡 The "reception can view SOAP" per-clinic toggle exists in the DB/API but has no Settings UI — the configurability `mvp.md` §6.11 promises is backend-only.
- 🟡 Multi-clinic login picks an arbitrary membership with no deterministic order.
- 🟡 No "resend invitation" — only revoke-and-recreate.
- 🟡 No session management (no "log out everywhere," no active-sessions list).
- ⚪ Notification preferences are clinic-wide only, no per-user opt-outs.
- Audit log itself (data model + backend filters) is solid — not a redesign target on its own; only its UI needs work (§1.4).

### 1.2 Patients, Scheduling, Public Booking, Waiting Room, Recurring/Walk-ins

- 🔴 No patient dedupe/merge — duplicate charts are permanent once created, with no lookup-before-create and no merge tool.
- 🔴 Insurance/HMO fields exist in the data model and API but are never collected or displayed in the patient UI.
- 🔴 No CSV/spreadsheet patient import — a clinic migrating off paper/Excel must hand-enter every patient.
- 🔴 Public booking requests land directly in the normal appointment list/calendar with no pending-review queue or visible "came from public link" badge — staff must eyeball every row to catch new requests.
- 🔴 No cancellation waitlist.
- 🟡 Doctor selectors across booking/calendar/walk-in show `specialty` or a raw UUID instead of the doctor's name — multi-doctor booking is confusing exactly where `mvp.md` §7.1 said it mattered most.
- 🟡 Calendar has no true multi-doctor side-by-side/resource view — only a single-select filter or a color blend.
- 🟡 `room_id` exists on the model but has zero UI — multi-room clinics can't schedule or view by room.
- 🟡 No appointment type/service catalog tied to scheduling (duration/fee) — every booking is a generic hand-configured slot.
- 🟡 Patient profile has no appointment/visit history tab or synthesized timeline — no "360 view."
- 🟡 No queue reordering/priority in the waiting room.
- 🟡 Appointment list has no date range, status, or doctor filter/search.
- ⚪ Recurring series only support fixed weekly/biweekly/monthly presets capped at 12 occurrences, no custom end date.
- Global patient search (command palette, fuzzy match) and the walk-in/waiting-room forward-flow are solid — not redesign targets.

### 1.3 Clinical — SOAP, Prescriptions, Chart Search, Visit Summaries, Transcription

- 🔴 Allergies are edited as a raw JSON textarea; chronic conditions, current medications, and vaccination history have **zero UI anywhere** despite existing as model fields. This makes the AI drug-interaction check dead in practice (it reads a field no one can ever populate).
- 🔴 The drug-interaction "database" is 8 hardcoded drugs seeded in a migration — any other prescription gets no safety check, with no visual indication that it wasn't checked.
- 🔴 No lab/imaging order lifecycle at all — no model, no status, no way to attach results back. "Orders" are one-off PDFs with no tracking.
- 🔴 Referral tracking has the same gap — no recipient/sent/outcome fields, just a PDF.
- 🔴 The AI Visit Summary silently falls back to a hardcoded, patient-generic paragraph on any failure, with no warning shown to the reviewing doctor — a placebo message could be approved and sent believing it reflects the real visit.
- 🟡 Specialty templates cover only General/Dental/Pediatric — OB-GYN, psychiatry, dermatology (all named target specialties) have none.
- 🟡 The two specialty fields that do exist (tooth chart, growth percentile) are single free-text boxes, not real charting tools (no per-tooth diagram, no plotted growth curve).
- 🟡 Chart versions render as a flat link list with no diff/comparison view between versions.
- 🟡 E-signature is applied on SOAP and Rx PDFs but never on certificates/referrals.
- ⚪ Transcription runs the smallest/lowest-accuracy Whisper model tier.
- ⚪ ICD-10 lookup is a static 5-code array, not a real search.
- AI SOAP drafting UX itself (streaming, "review before saving" framing, clears on manual edit) is genuinely good and not a redesign target.

### 1.4 Billing, Documents, Reminders, Recalls, Reports, Audit Log

- 🔴 No invoice correction path after payment — no void-with-payment, refund, or credit-note flow. Billing mistakes can never be fixed in-app.
- 🔴 SMS reminders never call Twilio (logged stub only) while Settings presents a working-looking credentials form — a silent, confidence-breaking failure.
- 🔴 No clinic-wide outstanding-balance or invoice list — only a 5-row dashboard widget and per-patient invoice routes; front desk cannot see "all unpaid invoices today."
- 🔴 BIR Official Receipt numbering (prefix/next number/pad width) has no API route or UI — only a seed script and internal mutation.
- 🔴 Recall campaign rules (e.g. "diabetic patients, every 3 months") are read from a config object that has no Settings control anywhere — the feature only works via a hand-crafted API call.
- 🟡 Reports group "by doctor" using a raw UUID instead of a name.
- 🟡 No drill-down from a report bar/period to the underlying appointment/invoice records.
- 🟡 Zero staff-facing reminder delivery visibility — no sent/failed/pending status, no retry, no per-patient opt-out.
- 🟡 HMO/insurance claims are two loose text fields with no status or clinic-wide claims list.
- 🟡 Audit log filters require exact internal action/type strings (free-text) instead of dropdowns — impractical for a non-technical owner.
- 🟡 Document template editor is a WYSIWYG (TipTap) with token chips, Placeholders dialog, and sample preview. Logo/signature image upload in the letter body is still out of scope (clinic letterhead handles branding).
- 🟡 Service/fee catalog (has full backend CRUD) has no post-onboarding settings page to manage it.
- ⚪ Generated PDFs (invoices, documents) are plain text with silent truncation on long lines, no logo, no BIR-standard disclaimer/TIN fields.

### 1.5 AI Clinic Assistant (staff) + Patient-facing Assistant + Visit Summary + No-show

- 🔴 **Neither assistant has a real LLM/tool-calling loop wired in production** — see §0. This is the single highest-priority fix in this entire plan given it's the named flagship feature.
- 🔴 Confirm cards render only the raw tool name (e.g. `PROPOSE_CANCEL_APPOINTMENT`) with Confirm/Cancel buttons — the actual proposal payload (patient name, date, content) is sent by the backend but never displayed. Users would confirm actions blind.
- 🔴 The context model (`page_context`/`attached_context`) is spec'd, backend-supported, but never sent by the frontend — cross-scope safety and "act on the patient I'm viewing" can't function in real usage.
- 🟡 Documented tier escalation for booking risk (outside working hours, double-booking risk → Tier 2) isn't implemented — only clinical-write/external-send/bulk/cross-scope are checked.
- 🟡 No rich chat cards (patient/appointment/invoice) — everything renders as plain text, contrary to spec.
- 🟡 No discoverability — one-line empty state, no suggested prompts, no onboarding.
- 🟡 No AI usage/cost visibility for clinic owners, and no per-tool enable/disable (only one global boolean).
- 🟡 Weak error UX on tool failures (raw backend error strings, no retry).
- ⚪ No-show risk scoring is real and works, but only surfaces "high" risk with no reasons shown, and isn't wired into reminder timing (smart reminder timing from §8.8 is unimplemented).
- The audit-log integration (`actor_type=ai_assistant` filter) and the patient-assistant's grounding/safety sanitization are both genuinely solid — not redesign targets on their own, just currently moot given the LLM-wiring gap.

### 1.6 Platform/SaaS layer, Navigation, Design System, Mobile/PWA, Ops readiness

- 🔴 **Confirmed fully absent** (grepped, not assumed): Super Admin role/panel, subscription/plan/tier model for clinics (no `plan`/`status` column on `Clinic` at all), any operator view to onboard/suspend/offboard a clinic, a UI for the AI kill switch (env-var only, requires a deploy to flip), cross-clinic analytics (explicitly a documented invariant that none exists), impersonation/support-login tooling, and a pricing/plan-selection page. **There is no lever to sell, bill, support, or cut off a tenant.**
- 🔴 12 of 17 items in `mvp.md` §12's Production Readiness Checklist are still unchecked, including the backup **restore drill**, uptime monitoring/alerting, a PHI-in-logs spot check, and physical print-fidelity testing — despite every phase being marked "Done."
- 🟡 PWA is scaffolded but dead code — `registerPwa()` is defined and never called anywhere.
- 🟡 Billing and document generation have no top-level nav entry at all (only reachable as nested patient sub-routes) — a receptionist looking for "Billing" as a module won't find it.
- 🟡 Design tokens are split across three sources (`DESIGN.md`, `docs/architecture/design-system.md`, `styles.css`) that disagree with each other (font choice) — no single enforced source of truth.
- 🟡 Mobile responsiveness is inconsistent page-to-page (e.g. `InvoiceDetailPage.tsx` has zero responsive classes) rather than systematically absent.
- ⚪ Navigation grouping itself (Overview / Patient care / Clinical / Insights / Settings) is reasonably sound — the redesign should extend it (add Billing, add Platform Admin as a separate app shell) rather than flatten and rebuild it from zero.

---

## 2. Redesign principles

1. **Fix what's silently broken before building what's new.** A feature that lies about working (SMS stub, AI assistant, visit summary fallback) is worse than a feature that doesn't exist, because staff build workflows around the lie. These come first regardless of how "done" they look in the phase tracker.
2. **Every field that's collected must be editable and visible somewhere.** No more allergy-as-JSON-textarea, no more HMO data with no form. If it's in the schema, it needs a real UI or it should come out of the schema.
3. **A clinic is a tenant; DoctorDesk is a platform.** From this plan forward, every clinic-facing feature and every platform-facing feature are two different apps sharing a codebase — a `Clinic.status`/`plan` model and a Super Admin surface are foundational, not a bolt-on.
4. **No raw internal identifiers in front of a user.** Doctor UUIDs, tool-name constants, and unexplained JSON are all bugs, not acceptable defaults.
5. **AI features must degrade honestly.** If a model call fails, the UI must say so — never substitute a canned answer that looks personalized.
6. **Keep the existing IA where it's already working** (patients/clinical/insights/settings grouping is sound) and extend deliberately — a full nav rebuild for its own sake would be scope for scope's sake, contradicting `CLAUDE.md`'s stance against premature rework.
7. **Every phase ships against the existing gates** (`pnpm run ci:quality`, RBAC re-checked server-side, `clinic_id` scoping, activity_log on mutations, mobile at 375–1024px, docs updated in the same change) — this plan does not relax any standing rule in `CLAUDE.md` or `docs/phases/README.md` §"Cross-cutting rules."

---

## 3. New information architecture

Two separate app shells from this point forward, both served from this monorepo:

```
doctordesk.app                          admin.doctordesk.app (or /platform/*)
──────────────────────                  ──────────────────────────────────
Clinic app (existing, refined)          Platform app (net new, Super Admin only)
├─ Overview (dashboard)                 ├─ Tenants (clinics) — list, detail, suspend/reactivate
├─ Patient care                         ├─ Plans & billing — plan catalog, clinic subscriptions,
│  ├─ Patients                          │  invoices to clinics (the SaaS side, distinct from §6.7's
│  ├─ Appointments (list + calendar)    │  clinic→patient billing)
│  ├─ Waiting room                      ├─ Usage & cost — AI usage, SMS usage, storage, per clinic
│  └─ Recalls                           │  and platform-wide
├─ Clinical                             ├─ Feature flags & kill switches — AI assistant toggle,
│  ├─ Chart search                      │  per-feature rollout, no deploy required
│  └─ (SOAP/Rx reached from a visit)    ├─ Support tools — impersonate/support-login (fully audited),
├─ Billing  ← NEW top-level entry       │  ticket/escalation notes per clinic
│  ├─ Invoices (clinic-wide list)       ├─ Platform analytics — cross-clinic aggregate metrics
│  └─ Claims (HMO)                      │  (counts/health, never patient content)
├─ Documents  ← NEW top-level entry     └─ Platform audit log — every Super Admin action, append-only
│  ├─ Generate
│  └─ Templates
├─ Insights
│  ├─ Reports
│  └─ Audit log
└─ Settings
   ├─ Clinic (NEW — hours/holidays/branding, ongoing)
   ├─ Team
   ├─ Doctor profile
   ├─ Services & fees (NEW — post-onboarding catalog editor)
   ├─ Notifications & recall rules
   ├─ Assistant
   └─ Billing plan (NEW — this clinic's own subscription/plan, upgrade/downgrade)
```

Public-facing surfaces (unchanged shells, refined content): public booking page, public reminder page, and a new **pricing/signup page** (`/pricing`, feeds registration with a plan selection instead of registration creating a plan-less tenant).

---

## 4. Phased build plan

Numbering continues from `docs/phases/19` (the existing MVP build). Each phase below is written at PRD depth for the design/scoping. **When a phase is picked up for execution, write it as a full phase file under `docs/phases/phase-NN-<slug>.md` matching the existing format** (goal, prerequisites, backend/frontend/DB tasks, edge cases, testing, docs to update, exit criteria) before coding — this document is the sequencing and requirements source, not a replacement for that format.

Priority key: 🔴 = do first (trust-breaking or go-live blocking), 🟡 = do next (usability/completeness), ⚪ = defer until the above are done.

### Phase 20 — Trust repairs (🔴, no new modules, fix what lies)

Goal: nothing in the product should silently fail or claim to work when it doesn't.

- Wire a real LLM tool-calling loop into the staff AI assistant (`app/ai/assistant/service.py`/`orchestrator.py`) — replace the `__tool__:` literal-parsing shim with actual PydanticAI structured tool-calling, matching the pattern already proven in `app/ai/soap_draft_service.py`.
- Remove the `DOCTORDESK_TESTING` gate on the patient-facing assistant's write tools (`patient_assistant/service.py`) and wire the same real tool-calling loop there.
- Implement real Twilio SMS sending in `reminder_service.py` (or clearly disable/hide the SMS credentials UI in Settings until it does) — no more `"twilio-stub"`.
- Fix the AI Visit Summary to surface failure honestly: if generation fails, show the doctor an explicit "AI summary unavailable — write manually" state instead of a generic canned paragraph (`visit_summary_service.py`, `VisitSummaryPanel.tsx`).
- Add the PRC-license/signature completeness gate to `document_service.py` (certificates/referrals), matching `prescription_service.py`'s existing check.
- Exit criteria: a real (non-test) user can drive both assistants with natural language and get correct tool execution; an SMS reminder either really sends or the feature is visibly off; a failed AI visit summary is never mistaken for a real one.

### Phase 21 — Account & session foundations (🔴)

- Forgot-password / reset-password flow (API + email + UI), email verification on registration.
- Data export (patient list, appointment history, CSV) and an account/clinic data-deletion request path per `mvp.md` §6.12 and PH Data Privacy Act.
- Session management: "log out everywhere," active-sessions list.
- Deterministic multi-clinic membership ordering at login + a clear clinic switcher entry point.
- "Resend invitation" action; pending-invite visibility improvements.
- Exit criteria: no account is ever permanently unrecoverable; a user can see and revoke their own sessions; a clinic can export and delete its own data on request.

### Phase 22 — Settings that actually reach production (🔴/🟡)

- New Settings → **Clinic** page: hours, holidays, branding (logo, address, letterhead), editable anytime post-onboarding.
- New Settings → **Services & fees**: full CRUD UI over the existing `ServiceFee` backend.
- Settings → RBAC: real checkbox for `reception_can_view_soap`.
- Settings → **Recall rules**: UI for `chronic_condition_rules` (condition → interval), replacing the hand-crafted-API-only path.
- Settings → **Receipt numbering**: UI + API route for BIR OR prefix/next-number/pad-width.
- Document template editor: placeholder picker, live preview, logo/signature image upload.
- Exit criteria: every clinic-level configuration item that exists in the backend has a reachable, real Settings UI.

### Phase 23 — Patient record integrity (🔴)

- Patient dedupe: lookup-before-create by phone/name with a "possible match" prompt; a merge tool for existing duplicates.
- Real forms for insurance/HMO, structured allergies (chip/tag input, not JSON), current medications, chronic conditions, vaccination history (dated, structured entries) — replacing the JSON textarea and the unreachable fields.
- CSV/spreadsheet patient import with a review-before-commit step.
- Patient profile: add an Appointments/visit-history tab and a synthesized timeline (appointments + SOAP + Rx + billing on one page); make demographics editable in place.
- Exit criteria: every patient-medical field in the data model has a real, structured UI; the AI drug-interaction check has real data to check against.

### Phase 24 — Scheduling & booking that scales past one doctor (🔴/🟡)

- Doctor selectors everywhere show `full_name`, never specialty-as-fallback or a UUID.
- Appointment type/service catalog wired to scheduling (duration + fee default from type, not hand-typed every time).
- Multi-doctor side-by-side/resource calendar view; room scheduling wired into the UI wherever `room_id` already exists on the model.
- Public booking: a staff-facing pending-requests queue distinct from confirmed appointments, with a clear "from public link" badge.
- Cancellation waitlist (patient wants an earlier slot).
- Appointment list: date range, status, doctor filters and search.
- Exit criteria: a 3-doctor, 2-room clinic can run its entire day from the calendar without confusion about who's who or which room is free.

### Phase 25 — Clinical safety and specialty depth (🔴/🟡)

- Replace the 8-drug hardcoded interaction seed with a real drug/interaction reference source (evaluate a licensable drug database or an established open dataset) and make "not checked" visually explicit for anything outside coverage.
- Lab/imaging order lifecycle: a real entity (ordered → in-progress → resulted), attach results back to the order and the patient's files.
- Referral tracking: recipient, sent status, outcome fields, not just a PDF.
- Specialty templates for OB-GYN (obstetric history/EDD), psychiatry, dermatology; real charting widgets for the existing dental (tooth chart) and pediatric (growth curve) sections instead of free-text boxes.
- Chart version diff/comparison view.
- Apply the e-signature consistently to certificates/referrals, not just SOAP/Rx.
- Exit criteria: the clinical safety story (allergy/interaction checks) is real for the drugs a target clinic actually prescribes; every named target specialty has a template that reflects real clinical structure, not a relabeled textarea.

### Phase 26 — Billing integrity (🔴)

- Invoice correction workflow: refund/credit-note/adjustment path for a paid invoice, with an audit trail (not blind void).
- Clinic-wide invoice list and outstanding-balance list — sortable, filterable, exportable — as a real top-level Billing section (see §3 nav).
- HMO/insurance claims as a real status-tracked list (submitted/approved/denied/paid), not two loose text fields.
- Exit criteria: a front desk can answer "who owes us money right now, clinic-wide" and "how do I fix yesterday's billing mistake" without leaving the product or asking an engineer.

### Phase 27 — Communications you can trust (🟡, depends on Phase 20's real SMS sending)

- Staff-facing reminder delivery dashboard: sent/failed/pending status, retry a failed send, per-patient opt-out.
- Wire "smart reminder timing" to the existing no-show risk score (currently computed but unused for timing) per `mvp.md` §8.8.
- Exit criteria: staff have visibility and control over every reminder the system claims to send.

### Phase 28 — Reports and audit that non-engineers can use (🟡)

- Fix "by doctor" grouping to show names, not UUIDs, across all reports.
- Add drill-down from a report period/bar to the underlying appointment/invoice records.
- Rebuild Audit Log filters as dropdowns (actor, action category, target type) instead of free-text internal strings.
- Exit criteria: a clinic owner with no technical background can self-serve both reports and the audit trail.

### Phase 29 — AI Clinic Assistant v2, made trustworthy and discoverable (🔴/🟡, depends on Phase 20's real tool-calling)

- Confirm cards render the actual proposal payload (patient name, date/time, content) — never a raw tool-name constant.
- Wire `page_context`/`attached_context` from the frontend composer so cross-scope safety and "act on what I'm viewing" work as designed.
- Implement the documented working-hours/double-booking-risk tier escalation for booking proposals.
- Rich chat cards (patient/appointment/invoice) replacing plain text.
- Discoverability: suggested-prompt chips, first-run tooltip.
- Clinic-owner-facing AI usage/cost view; per-tool enable/disable beyond the single global toggle.
- Better tool-failure UX (clear message + retry).
- Exit criteria: a real receptionist, with no training beyond "there's a chat button," can book an appointment, check a balance, and cancel a visit through the assistant, sees exactly what they're confirming every time, and a clinic owner can see what the AI has been doing and what it's costing.

### Phase 30 — Platform layer: Super Admin, tenancy, and monetization (🔴, entirely new)

This is the module named explicitly by the product owner as missing. Scope:

- **Tenant model**: add `status` (`trial` / `active` / `suspended` / `cancelled`) and `plan`/`tier` to `Clinic`; a clinic with `status=suspended` is locked out at auth/middleware level, not just hidden in the UI.
- **Super Admin role**: platform-level, separate from the clinic-scoped `owner/admin/doctor/reception` roles, gated by its own auth boundary (not just a clinic membership check).
- **Platform app shell** (`/platform/*` or a separate subdomain): tenant list/search/detail, suspend/reactivate, plan changes.
- **Plans & billing**: a plan catalog (what a clinic pays DoctorDesk — distinct from §6.7's clinic→patient billing), a subscription record per clinic, and a pricing/plan-selection step added to signup (currently registration creates a plan-less tenant with no monetization hook at all).
- **Feature flags / kill switches with a real UI**: the AI assistant's platform-wide toggle (currently an env var requiring a deploy) becomes a Super Admin control, plus per-feature rollout flags for future launches.
- **Usage & cost visibility**: AI usage, SMS usage, storage, per clinic and aggregated — the data already exists in `ClinicAiUsage`; it just needs a platform-facing view.
- **Support tooling**: an audited impersonation/support-login flow so support staff can help a clinic without direct DB access, with every use logged to a platform audit log distinct from the clinic's own `activity_log`.
- **Platform analytics**: cross-clinic aggregate health/usage metrics — counts and trends only, never patient content, preserving the existing "no cross-clinic query" data-model invariant for anything patient-scoped.
- Exit criteria: DoctorDesk can be operated as an actual SaaS business — sell a plan, onboard a tenant, see how it's doing, help it when it's stuck, and cut it off if it needs to be cut off — without an engineer touching the database.

### Phase 31 — Mobile, PWA, and design-system consolidation (🟡)

- Wire `registerPwa()` into the actual app entry point; verify install-to-home-screen works on a real tablet.
- Systematic responsive pass over pages the audit flagged as inconsistent (starting with `InvoiceDetailPage.tsx`), reusing patterns already proven elsewhere (`Table`, `WaitingRoomBoard`).
- Consolidate design tokens into one enforced source of truth; resolve the font/token disagreement between `DESIGN.md`, `docs/architecture/design-system.md`, and `styles.css`.
- Exit criteria: a front-desk tablet user gets a consistent, installable, touch-friendly experience on every screen, not just the ones that happened to get attention.

### Phase 32 — Production readiness closeout (🔴, gate before any real pilot clinic)

- Close every remaining unchecked item in `mvp.md` §12: run and document an actual backup restore drill, configure uptime monitoring/alerting, do a PHI-in-logs/Sentry spot check, verify print fidelity on real paper for Rx/certificates/invoices/SOAP exports.
- Run a full RBAC and AI-safety regression pass against the rebuilt assistant (Phase 29) and the new platform layer (Phase 30) specifically, since both are net-new trust boundaries.
- Exit criteria: every box in `mvp.md` §12 is checked with real evidence, not "code exists so it's done."

---

## 5. Sequencing rationale

Phases 20–22 come first because they fix things that are actively misleading users or leave accounts unrecoverable — shipping anything else on top of a lying AI assistant or an unrecoverable login is wasted work. Phases 23–28 rebuild the clinic-facing modules in the order a clinic actually depends on them (patients → scheduling → clinical → billing → communications → reporting). Phase 29 revisits the AI assistant only after its underlying tool-calling is real (Phase 20) and its data is trustworthy (Phases 22–28 feed the tools it calls). Phase 30 (platform/Super Admin) is scoped as its own late-but-critical phase because it's additive — it doesn't block a single clinic from using the product — but it blocks running DoctorDesk as a multi-tenant business, which the product owner explicitly flagged as a requirement. Phases 31–32 are hardening passes that make sense once the functional surface has stopped changing.

If timeline pressure forces a smaller first cut, the non-negotiable subset is **Phase 20 in full** (nothing should keep lying), the 🔴 items inside Phases 21–26, and Phase 32 — that combination is the actual difference between "looks done" and "safe to hand to a real clinic."

---

## 6. Open decisions needed before phases 26/30 can be scoped in full

Carried over/sharpened from `mvp.md` §15, now blocking specific phases above:

1. **DoctorDesk's own pricing model** (Phase 30) — subscription tiers, trial length, what's metered (AI usage? SMS?) vs. flat-rate. Cannot build the plan catalog without this.
2. **Drug/interaction reference source** (Phase 25) — a licensable commercial database vs. an open dataset vs. a curated expanded list; cost and licensing implications differ substantially.
3. **SMS provider go-live** (Phase 20/27) — confirm Twilio is still the intended provider and who owns the per-clinic cost, per `mvp.md`'s already-open question.
4. **Support/impersonation policy** (Phase 30) — what a support agent is allowed to see/do while impersonating a clinic user, and patient-consent implications given PHI is involved.
5. **BIR/local compliance specifics** (Phase 22/26) — confirm the exact OR numbering rules and required invoice fields with an accountant/compliance resource before building the UI, not after.

---

## 7. What this plan deliberately does not touch

Everything in `mvp.md` §14 (Out of Scope for MVP) stays out of scope here too — this is a redesign of what already shipped, not a scope expansion into telemedicine, live voice AI, native mobile apps, or multi-branch franchise management. The Super Admin/platform layer in Phase 30 is the one addition beyond `mvp.md`'s original boundary, justified because it's required to operate the product as a business at all, not a feature nice-to-have.
