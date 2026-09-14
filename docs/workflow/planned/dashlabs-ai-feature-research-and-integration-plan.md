# Dashlabs.ai competitive research — feature inventory & integration plan

**Status:** Research complete (docs + 41s reel + 7-min Basic 5 tutorial, 2026-09-14), awaiting decisions in §6 before anything is scheduled.
**Type:** Market/competitive research pass, not an engineering plan — produces a prioritized feature backlog to fold into `docs/mvp.md` and `docs/phases/` after the open decisions in §6 are resolved with the user. Follows the same method as [`clinic-software-market-research-feature-gaps.md`](./clinic-software-market-research-feature-gaps.md) (Phases 33–39), which this doc extends rather than repeats.
**Do not implement from this document directly** — this identifies gaps and opportunities; it does not design the implementation. Each accepted item still needs its own spec pass against `docs/mvp.md`'s conventions (data model, RBAC tier, AI tool tier if applicable, doc updates) before it becomes a phase.
**Scope of the ask:** research everything Dashlabs.ai offers (site, pricing, public docs, press, video/social content where accessible), list every feature, and identify (a) which of their features we should adopt, and (b) how kame-desk can go further than they do by layering real generative-AI on top — since kame-desk already ships an LLM-based AI Clinic Assistant and Dashlabs, despite the ".ai" name, does not.

---

## 1. Method, sources, and a correction to the starting assumption

**What was requested:** crawl `dashlabs.ai`, watch a YouTube tutorial video (`OG8cdGDXiT0`) and a Facebook reel, and extract every feature shown.

**Pass 1 (docs):** feature existence and module structure from Dashlabs' public documentation (`help.dashlabs.ai` `llms.txt`), marketing site (home, pricing, solutions), Y Combinator profile, and press. That pass could not watch video: the YouTube page returned chrome only, and the Facebook reel URL was login-walled.

**Pass 2 (2026-09-14, 41s reel):** vertical clinic walkthrough transcribed with Whisper tiny and checked against captions plus 1 fps frames. Shot at **Menara Health Diagnostics** on `dashlabs.app`. Full notes in §3.12.

**Pass 3 (2026-09-14, Basic 5 tutorial):** local MP4 of **"Dashlabs Basic 5 Tutorial Video"** (`OG8cdGDXiT0`), 6:59, 1280×712. Transcribed with Whisper base; UI confirmed from frames every 3s on the **Dashlabs Demo Site**. This is the product-setup + cashier + queue + results + reports walkthrough the reel only named. Full notes in §3.13.

**Confidence level:** High for feature existence (docs + pricing). High for both videos' click-paths. Lower for Enterprise-only flags that never appear on screen (e.g. whether **PhilHealth professionals** is e-claims or just a doctor list).

Full source list in §8.

---

## 2. What Dashlabs.ai actually is (correcting the initial premise)

The initial assumption going in was that dashlabs.ai is an AI scheduling/receptionist tool. **It is not.** Dashlabs.ai is a **cloud-based Laboratory Information System (LIS) and clinic management platform**, built in Manila, targeting **diagnostic laboratories, medical centers, veterinary clinics, dialysis centers, hospitals, and corporate Annual Physical Exam (APE) / Pre-Employment Medical Exam (PEME) providers** processing 50–5,000+ patients/day, primarily in the **Philippines, Indonesia, and Malaysia**.

- Founded 2020 (Bryan Giger, Martin Gomez, Weston Coleman Lim), Y Combinator W21, ~~₱65M (~~$1.2M) seed raised Feb 2022, ~30 employees, 200+ clinics live.
- Their core pitch is **operational automation of lab/diagnostic throughput** — one press piece cites clinics going from 7–14 days to process 500–1,000 patients down to 24–48 hours after adopting Dashlabs, largely via machine integration and workflow automation, not generative AI.
- **Despite the ".ai" brand, the public marketing site makes zero explicit claims of AI/ML/LLM features.** "AI" in their positioning is journalistic shorthand for _automation_ (auto-ingesting analyzer results, auto-routing queues), not artificial intelligence in the sense kame-desk means it (drafting, summarizing, chatting, predicting). This is the single most important strategic finding in this research — see §5.

This makes Dashlabs a genuinely useful **operational-workflow** reference (queue routing, corporate bulk workflows, device integration, multi-branch ops) but **not** an AI reference. kame-desk should borrow their operations patterns and pair them with kame-desk's own real AI stack — something no competitor found in either this research pass or the prior one (`clinic-software-market-research-feature-gaps.md`) is doing.

---

## 3. Full feature inventory (as documented by Dashlabs)

### 3.1 EMR Module

- **Patient records** and **Patient Service records** (a "service" = a test/procedure a patient avails — bloodwork, consult, imaging), modeled as one patient → many services.
- Add/manage patient record; patient search by name or barcode (exact match only, not fuzzy).
- **Online Patient Registration Form** — patient fills a customizable form remotely or on-site (medical history, insurance, consent); data flows directly into the EHR/LIS with no manual re-entry; no-code setup, launches "in minutes."
- **QR-at-door self-registration (video-confirmed, §3.12)** — a branded poster at reception ("SCAN TO REGISTER") opens the clinic's own digital form on the patient's phone. The patient types demographics themselves; front desk does not re-key. This is the same online form as above, distributed as a QR, not a kiosk app.
- **Staff-side registration (tutorial-confirmed, §3.13)** — Cashiers → Register New Patient: photo upload or **camera capture**, first/middle/last name, suffix, birthday, sex, email. Cashier also has **Scan QR code** (accession: retrieve an already-registered patient) and name search.
- **Homepage patient IA (tutorial, not clicked through):** Form, Accession, Patients, Patient services, **Patient cases** (a group of services belonging to one patient), **Partners** (corporate management), **Plans** (track insurance, benefits, and consumption).

### 3.2 Patient Service Management (results workflow)

- Patient Service page: enter results, modify settings, release results.
- **Results Input Forms** — customizable per service type (lab, imaging, consultation), field types include quantitative, qualitative, binary (yes/no), and file attachment; supports reference ranges/normal values and preset dropdowns; no coding required.
- **Result locking** — once encoded, results can be locked to prevent edits; unlocking requires explicit authorization.
- **Result Documents** — PDF certificate generation, auto-attached e-signatures via a **Signatories** feature (role-gated — e.g. only pathologist/radiologist signatures), email delivery, optional encrypted-email add-on.
- **Video-confirmed release path (§3.12):** branded lab PDF (clinic logo, address, QR on the certificate), pathologist signatures, one-click email, and the same PDF on the patient's phone at reception. Help docs also list "Release to patient dashboard."
- **Consults, prescriptions, and physical exams** are first-class patient services in the same web EMR (shown as a doctor laptop workflow in the reel, not a separate product).
- Patient Services table: filter by service type/date, customizable columns, print a linelist PDF, export selected rows to CSV.

### 3.3 Finance Module

- **Point of Sale ("Store Orders")** — cashiers record a sale; a completed order **auto-creates the linked Patient Service** (the trackable clinical order) and records the purchase price; receipts and barcodes print from the order.
- **One-screen cashier (video-confirmed, §3.12)** — patient header (name, generated ID, email, sex, DOB, age), purchase history, partner, line items (product, qty, unit price, amount), **Add products**, **Add discount / price increase**, **Add another patient** (group/family checkout on one ticket). Checkout metadata: referrer, tags, sales agent, reference number, notes. Thermal receipt prints queue number, receipt #, cashier name, items, and payment type.
- **Payment categories in one POS (video-confirmed)** — Cash, **HMO**, **Charge To** (company or named-doctor account), and **APE**. Tutorial cashier also shows **E_WALLET** and **BANK**, plus payment-proof upload/camera and **Add payment** (split tenders). Charge To lists named doctors as chargeable accounts. This is POS payment routing, not HMO eligibility/LOA automation (see prior PH research).
- **Product catalog (tutorial-confirmed, §3.13)** — Products have tabs Basic / Post-purchase / Display / Requirements / Bundled / Advanced. One SKU can carry **multiple price packages** (demo: Regular ₱500 and **HMO – Maxicare** ₱350), branch/store visibility, "show on cashier" and **"show on public store"**. **Post-purchase** attaches the patient services that a sale mints (Vital Signs, Physical Exam, Urinalysis, Fecalysis, Hematology → CBC variant, X-Ray → Chest PA). Optional calendar rule, queue server, and workflow on the same screen.
- **BIR disclaimer on cashier (tutorial-confirmed):** "This software is not BIR approved. This software is for order taking only. All BIR related calculation should be done by the user of this software." Dashlabs does not claim to solve PH receipt compliance.
- **Store Ledgers** — extend credit to corporate/institutional clients and track revenue per account (B2B accounts-receivable, distinct from per-patient billing).

### 3.4 Inventory Module

- Create inventory items: name, unit of measure (pieces or weight), a low-stock warning threshold, and assignment to a specific branch/location. Deliberately minimal — no lot/expiry tracking, no purchase-order workflow documented.

### 3.5 APE/PEME Module (corporate bulk-screening vertical)

- Built specifically for Annual Physical Exam / Pre-Employment Medical Exam volume: **bulk pre-registration** of many employees at once, **automated queue routing** at scale, **parallel results encoding** across stations simultaneously, **per-company billing** and post-event reporting.
- **Site Operations** sub-module (on-site/off-site event logistics) and a **Corporate Management Module** (managing employer/corporate accounts and exam packages).
- **Medical Evaluation + Fit to Work (tutorial-confirmed, §3.13):** a dedicated queue after labs/PE. Tabs across Profile / Vital Signs / Urinalysis / Fecalysis / Hematology / X-Ray. Diagnosis, recommendations, and **Fit to Work Classification**: Class A (fit), B (minor condition), C (major condition), D (unfit). Results can be compared side by side and copied into the PE record. This is occupational-health / APE, not a general SOAP note.

### 3.6 Workflow & Queue Engine — Dashlabs' most distinctive feature

This is the one genuinely novel piece of engineering found in this research, and the strongest candidate for adoption:

- **Workflow** = a visual flowchart builder mapping every station in the clinic (e.g. triage → specimen draw → imaging → doctor → billing → pharmacy) and how patients move between them. Configured per clinic (today, by Dashlabs' own onboarding team, not self-serve).
- **Five routing/connection types** between stations:
  | Type         | Behavior                                                                                                       |
  | ------------ | -------------------------------------------------------------------------------------------------------------- |
  | Automatic    | Patient auto-advances to the next station as `WAITING`                                                         |
  | Manual       | Patient goes to `NOT READY`; staff manually releases them to `WAITING`                                         |
  | Shortest     | Routes to whichever of several eligible next-stations currently has the shortest queue                         |
  | Intersection | Patient only advances once _multiple_ upstream stations are all complete/ready                                 |
  | Concurrent   | Patient enters _all_ eligible next-stations at once; once one starts serving, the others revert to `NOT READY` |
- **Queue** = the live operational workspace per station: split-pane UI (patient list left, action panel right), per-patient status (`Not Ready` / `Waiting` / `Serving` / `Complete`), a "call patient" button, elapsed-time indicators, clinic-presence/check-in verification, a calendar-view toggle for scheduled vs. walk-in, and filters by status/schedule/priority/assigned staff/workflow stage/staleness.
- **15+ configurable "action widgets"** per station — patient info, service/task tracking, result input, activity log, workflow map view, barcode tools, document download, third-party integrations — station screens are composed from these, not hardcoded per station type.
- **Admin queue settings**: per-station user access, widget selection/ordering, which services route through this station, display toggles (call/start buttons, scheduling), completion requirements, cashier/branch linkage.
- **Tutorial-confirmed UI (§3.13):** pin queue servers to the homepage; Call vs Start; queue ticket IDs (e.g. `JT-727`); **In clinic** badge; print per-test barcodes; **Now** stamp for specimen collected-at; assign the next station to a **named doctor**; Next Queues widget; Results Releasing station with per-service lock + bulk PDF download; Action task "Send email" (async, status Processing). Demo stations include Cashier, Reception, Nurse Station – Vital Signs, Laboratory Extraction/Results, Urine/Stool Collection, Fasting Extraction, Pathologist, SEND-OUT, ECG Collection/Reading, Ultrasound Image Collection/Reading, X-Ray Image Collection/Reading, Consultation & Physical Exams, Medical Evaluation. The workflow canvas is a React Flow graph with Automatic / Shortest / Manual labels on the edges.

### 3.7 User Access Control

- Linux-style permission primitives — **read / write / delete / send** — assignable **per individual user or per user group** ("Laboratory User Groups" = an RBAC-group layer), plus a distinct **Access Control Ruleset** object. More granular/composable than a fixed role list.

### 3.8 Notification Triggers

- Admin-configurable rules that fire **email and/or SMS** to patients on defined events (e.g., result released); an optional encrypted-email add-on for sensitive results.

### 3.9 Machine & Device Integrations

- Bidirectional integration with lab analyzers (Mindray, Sysmex, Beckman Coulter, Roche, others) and DICOM-enabled imaging equipment (X-ray, ultrasound) — results flow in automatically instead of being retyped. Sold as a metered hardware/software add-on ("Dashbox," ₱6,000/branch/month).
- **Video-confirmed path (§3.12):** Mindray **H360** hematology analyzer → patient record; barcoded request form on a clipboard; encode screen with signatory checkboxes and "Download documents"; branded CBC PDF with units, reference ranges, QR code, and pathologist signatures. Imaging uses a **built-in basic DICOM viewer** (their words on-screen), not a full PACS workstation. Same PDF is printable and viewable on the patient's phone.

### 3.10 Security & Compliance

- Encryption at rest and in transit, a VAPT (penetration testing) program, and explicit **Philippine Data Privacy Act** compliance posture.
- **PhilHealth professionals** appears as a settings row on the homepage ("Configure philhealth professionals"). Not demoed in either video. Treat as a named surface, not proof of PhilHealth e-claims / HITP certification.
- Cashier explicitly **disclaims BIR approval** (§3.3). Logo, address, timezone (`Asia/Manila`), currency (PHP), and date-time format live under Organization settings; Superuser-only: org status, access rules, org record types, activation files, **white label**.

### 3.11 Packaging & pricing model (a go-to-market pattern, not a feature)

| Tier                             | Price                                                                                                             | What it unlocks                                                                                           |
| -------------------------------- | ----------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------- |
| Free                             | ₱0/mo                                                                                                             | Basic EMR, basic templates, online registration, 24-hour-only reports, Dashlabs watermark on certificates |
| Base CMS                         | ₱2,800/mo per branch                                                                                              | Custom forms, email delivery, full-history reports, e-signature attach, user roles, no watermark          |
| Add-ons (à la carte, per branch) | Machine Integration ₱6,000 · Ledgers & Sales Agents ₱3,000 · Queue Board ₱6,000 · Calendars & Appointments ₱1,500 | Each major module is a separately metered add-on rather than bundled into one tier                        |
| APE/PEME                         | Invite-only                                                                                                       | The corporate bulk-screening vertical, sold as a custom enterprise engagement                             |
| Enterprise                       | Custom                                                                                                            | Machine integrations, custom billing, whitelabel, dedicated support                                       |

Notably, **"Calendars & Appointments" is itself a paid add-on, not part of the base product** — scheduling is treated as secondary to their real core (lab results processing), which confirms Dashlabs is not a scheduling/booking competitor to kame-desk in the way the original ask assumed.

### 3.12 Observed clinic walkthrough (41-second reel, 2026-09-14)

Vertical social demo, ~41s, filmed at Menara Health Diagnostics. Hosted app is `dashlabs.app`. Cashier URL pattern: `Home > Cashiers > {branch} POC 1`. Narration below is Whisper tiny, corrected against on-screen captions ("Charge To" not "Charge 2"; "basic DICOM viewer" not "basic.com viewer").

| Time | Narration / caption                                                                              |
| ---- | ------------------------------------------------------------------------------------------------ |
| 0:00 | This is your clinic's workflow in 30 seconds with Dash EMR.                                      |
| 0:03 | Patients register using your own digital forms.                                                  |
| 0:06 | They scan a QR code and enter their details.                                                     |
| 0:09 | Cashier transacts your patient's order and payment in one screen.                                |
| 0:12 | You can track cash, HMO, Charge To, and APE payments in one system.                              |
| 0:18 | Doctors record consults, prescriptions, and physical exams directly in Dashlabs.                 |
| 0:22 | Laboratory tests go from machine into the patient record by LIS.                                 |
| 0:26 | Imaging results are captured the same way, and are viewable with built-in basic DICOM viewer.    |
| 0:31 | Results are ready as PDFs. You can email them in one click, because everything is in one system. |
| 0:36 | Sales census reports can be generated.                                                           |
| 0:38 | Start using Dashlabs now. Book a demo today.                                                     |

**UI and props actually visible (not just claimed):**

| Scene          | What is on screen                                                                                                                                                                                                                  |
| -------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Reception QR   | Branded poster: Menara Health Diagnostics, "SCAN TO REGISTER", QR. Patient's phone opens a pink/lavender branded form; they type fields (name visible). Suggestion box in frame is clinic furniture, not a product feature.        |
| Cashier POS    | Patient **GEMOTRA, MIGUEL MABANGIS**, ID `3004M87JL5C`, email, male, DOB Nov 1 1985, age 39. "This patient has no purchase history." Partner field. Item **Basic 5 – Regular**. Add products / discount / another patient.         |
| Checkout       | Referrer, Tags, Sales agent, Reference number, Notes. Payments: "Step 1: Select payment category." Charge To list includes **DEMO – CASH** and named doctors (consultation).                                                       |
| Receipt        | Thermal slip: queue number, **Receipt #2341**, cashier name, patient name, Basic 5 – Regular, payment DEMO – CASH, dated July 01 2025 3:26 PM. Epson-style printer + second printer on the desk.                                   |
| Doctor consult | Doctor at a laptop in an exam room; overlay: consults, prescriptions, physical exams in Dashlabs.                                                                                                                                  |
| LIS            | Tech at a **Mindray H360**. Encode UI: signatory checkboxes, Download documents, hematology fields. Clipboard with printed request + QR/barcode.                                                                                   |
| Result PDF     | **MENARA HEALTH DIAGNOSTICS** CBC: RBC/Hgb/Hct/WBC/neutrophils/lymphocytes/monocytes/platelets, units, reference ranges, QR on the report, pathologist signatures, "End of Report." Same PDF on paper and on a phone at reception. |
| Imaging        | Patient enters X-ray room (red warning light). Overlay: imaging captured the same way; built-in basic DICOM viewer on a desktop monitor.                                                                                           |
| Close          | "Sales census reports can be generated." CTA: book a demo.                                                                                                                                                                         |

**What this reel does _not_ show:** the visual workflow flowchart, queue split-pane, product catalog, inventory, APE bulk UI, ledgers, or RBAC. Those are in the Basic 5 tutorial (§3.13) or remain docs-only. Sales/census is named here, demonstrated as a report wizard in §3.13. No generative-AI surface in either video.

**Product-loop the reel is selling:** QR self-register → one-screen POS (cash / HMO / Charge To / APE) → doctor consult/Rx/PE → analyzer-to-chart LIS + DICOM → branded PDF (print + phone + email) → sales/census. That is diagnostic-lab throughput, not appointment-first clinic ops.

### 3.13 Dashlabs 101 / Basic 5 tutorial (6:59, 2026-09-14)

YouTube `OG8cdGDXiT0`, recorded on **Dashlabs Demo Site** (`dashlabs.app`). Header always shows Invite Members and Upgrade to Pro. This is the setup guide for the **"Basic 5"** package the 41s reel sold as "Basic 5 – Regular."

On-screen agenda: Add your logo · Add a Basic 5 product · Register a patient · Create a cashier transaction · Input results · Download and release results · Download sales reports.

**Cleaned transcript (Whisper base; Cushers→Cashiers, your analysis→urinalysis, ficalysis→fecalysis, Q servers→Queue servers):**

| Time | What they say / do                                                                                                                                                                                                                                                                                                          |
| ---- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 0:00 | Welcome to Dashlabs 101. Basics of the Dashlabs basic module.                                                                                                                                                                                                                                                               |
| 0:07 | Settings → pencil: upload organization logo (shown on reports, receipts, and the patient portal). Phone, address, email. Update.                                                                                                                                                                                            |
| 0:31 | Before registering a patient, create a product. Start with Basic 5. Products → Add Product → Add Price. Multiple prices for different customer types. Pick branches. Save.                                                                                                                                                  |
| 0:54 | Post-purchase → Add Patient Service. One product can mint many services. Add urinalysis, vital signs, physical exam, fecalysis. CBC via Hematology → Select Variants → CBC. Chest x-ray via X-Ray → PHS / Chest PA variant. Save.                                                                                           |
| 1:27 | Cashiers → main cashier. Register New Patient, fill fields, Submit. Search bar for already-registered patients. Add products, pick payment method, Add payment, Checkout. Print receipt (top right).                                                                                                                        |
| 2:39 | Check the workflow so every role can work as soon as the patient is ready and waiting.                                                                                                                                                                                                                                      |
| 3:00 | Pin Queue servers to the homepage: lab extraction and results (hematology, x-ray, fecalysis, urinalysis), nurse station, physical exams, medical evaluation.                                                                                                                                                                |
| 3:30 | Extraction queue: Call the patient. Click **Now** on the date to log extraction date/time, Save, Complete. Result queue: Call, type values from the machines, upload files, remarks text boxes. Signatories: dropdown of name/role/e-signature; uncheck e-signature to wet-sign. Save, download preview, **Save and lock**. |
| 4:45 | Physical exam: take vitals at the nurse-station queue first, then PE. Assign vitals to the right doctor. Medical evaluation compares all tests and can copy results into the PE record. Save before download or send.                                                                                                       |
| 6:07 | Print, or email if the patient gave an email. Click Complete.                                                                                                                                                                                                                                                               |
| 6:28 | Orders → Download. Pick date range, status **Paid**, file type, Download.                                                                                                                                                                                                                                                   |
| 6:51 | Close. Stay tuned for more videos.                                                                                                                                                                                                                                                                                          |

**UI confirmed in frames (not only claimed):**

| Area                     | What is on screen                                                                                                                                                                                                                                                                                                                                                                                                 |
| ------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Org settings             | Logo upload. Currency PHP. Business category `SINGLE_BRANCH`. Address, support email, timezone `Asia/Manila`, date-time format. Superuser: Org status, Access Rules, Org record types, Activation files, White label. Nav: Organization, Members, Member groups, Branches.                                                                                                                                        |
| Homepage IA              | Queues; Patients (Form, Accession = scan QR to retrieve patient, Patients, Patient services, Patient cases, Partners, Plans); Sales and accounting (Products, Stores); Inventory products; **PhilHealth professionals**. Pin-to-home on every row.                                                                                                                                                                |
| Product Basic 5          | Prices: Regular ₱500, **HMO – Maxicare** ₱350. Show on cashier / public store. Stores: DASHLABS, Branch 1 Store, Main Store. Post-purchase services: Vital Signs, Physical Exam, Urinalysis, Fecalysis, Hematology (CBC), X-Ray. Calendar rule / Queue server / Workflows. Product list columns: Templated, Category, Stores, Price package.                                                                      |
| Cashier                  | Search patient, Scan QR code, Register new patient. Photo upload + Camera. Fields: first/middle/last, suffix, birthday. Patient header + "Patient has no photo." Payments: **CASH, E_WALLET, BANK, HMO**. Charge to, amount, proof upload/camera, Add payment. BIR disclaimer. Receipt `JT-727` with org logo, address, phone, patient ID, DOB, sex, services, cash, cashier name, Print.                         |
| Workflow canvas          | React Flow graph. Stations: Laboratory Extraction, Urine/Stool Collection, ECG Collection, Ultrasound Image Collection, X-Ray Image Collection, Laboratory Results, Consultation & Physical Exams, Medical Evaluation, X-Ray Reading. Edge labels: Automatic, Shortest, Manual. Per-node status Waiting / Not ready. Patient picker.                                                                              |
| Queue servers (pinnable) | Cashier; Consultation & Physical Exams; ECG Collection/Reading; Fasting Extraction; Laboratory Extraction/Results; Medical Evaluation; Nurse Station – Vital Signs; Pathologist; Reception; SEND-OUT; Ultrasound Image Collection/Reading; Urine, Stool Collection; X-Ray Image Collection/Reading.                                                                                                               |
| Extraction queue         | Ticket `JT-727`, Call, Serving, In clinic, No priority. Print barcodes (`HEM605061`). Collected-at **Now**. View order. Search by task, order, or patient. List vs calendar.                                                                                                                                                                                                                                      |
| Lab results              | Numeric fields + reference range + units (e.g. reticulocyte count). Remarks + file upload. Three signatory slots with Display E-Signature and named staff.                                                                                                                                                                                                                                                        |
| Nurse / PE               | Vitals: respiration, O2 sat, temperature. Next Queues: assign Consultation & Physical Exams to a named doctor. PE is a ROS-style form (None/Yes dropdowns: colds, sore throat, SOB, cough, fever, chest pain, etc.).                                                                                                                                                                                              |
| Medical evaluation       | Tabs: Profile, Vital Signs, Urinalysis, Fecalysis, Hematology, X-Ray (image View/Download). Diagnosis, recommendations, Fit to Work Class A–D.                                                                                                                                                                                                                                                                    |
| Results releasing        | Per-service locks and Completed chips. Download selected PDFs (Hematology, Fecalysis, Urinalysis, X-ray Chest PA, Physical Exam). PDFs served from Google Cloud Storage. Action task: Send email, status Processing.                                                                                                                                                                                              |
| Sales reports            | Documents wizard: date range (last month / this month / today), stores, patients (name / retrieval code / plan number), status, members. Report types: Store Orders v2 CSV, Product Census PDF, Store Order Report (Product Merge) PDF, Store Order Report PDF/v2/CSV, Store Orders PDF, **Sales Performance Audit** PDF, **Product Volume Audit** PDF. Custom PDF templates (banner example: Laporan Penjualan). |

**What this tutorial still does not show:** machine/LIS ingest (the 41s reel does), DICOM viewer, APE bulk pre-registration, ledgers, inventory stock counts, PhilHealth claims submission, or any LLM/chat UI.

---

## 4. Gap analysis — mapped against current `docs/mvp.md` / `docs/phases/` scope

Legend: 🔴 Core gap worth closing · 🟡 Nice-to-have / strategic option, not a launch blocker · 🟢 Already covered or correctly out of scope, confirmed by this research — no action needed.

| #   | Feature (from §3)                                                                                                         | Verdict                            | Why                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| --- | ------------------------------------------------------------------------------------------------------------------------- | ---------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | **Multi-station configurable workflow & queue engine** (§3.6, §3.13)                                                      | 🟡                                 | Tutorial now shows the live React Flow canvas (Automatic / Shortest / Manual) and the split-pane queue: Call, ticket IDs, In clinic, barcodes, Now-stamp, pin-to-home, assign next station to a named doctor. kame-desk's waiting room is still one flat `Arrived → In Consultation → Completed`. Strongest feature to adopt for a 2–5 doctor clinic (nurse/vitals → doctor → billing), scoped down: 2–3 stations and 2 routing types, not their full station catalog. See §5 for the AI-enhanced version. |
| 2   | **Pre-visit digital intake/pre-registration form** that auto-populates the chart (§3.1, §3.12, §3.13)                     | 🟡 — needs verification            | Reel: QR poster, patient phone form. Tutorial: staff Register New Patient, camera photo, Scan QR accession, name search. Same destination (cashier already has the chart). Confirm whether kame-desk's public booking link and patient portal already capture this, or only scheduling info.                                                                                                                                                                                                               |
| 3   | **Corporate/group B2B accounts** — bulk pre-registration, per-company billing, Store Ledgers/credit accounts (§3.3, §3.5) | 🟡, strategic only                 | This is Dashlabs' single biggest structural difference (they built a whole vertical — APE/PEME — around corporate wellness/occupational-health screening). kame-desk's target user is a solo/small clinic serving individual patients, not corporate accounts. Only worth building if kame-desk decides to court occupational-health/corporate-wellness clinics as a segment — otherwise treat like multi-branch reporting: explicitly deferred (`mvp.md` §14), not silently ignored.                      |
| 4   | **Inventory module** (§3.4)                                                                                               | 🟢                                 | Already an explicit, reasoned deferral in `mvp.md` §14 with an open question at §15.2 (does any pilot clinic dispense medicine on-site?). Datapoint from this research: even a real competitor keeps inventory _deliberately minimal_ (name, unit, threshold, branch — no lots/expiry/PO workflow). This confirms kame-desk's own instinct — if/when built, keep it an "inventory-lite line item" per the existing open question, not a full inventory system.                                             |
| 5   | **Machine/lab-analyzer & DICOM device integrations** (§3.9)                                                               | 🟢                                 | Correctly out of scope. kame-desk's target users (`mvp.md` §3) are general/dental/specialty doctors running a clinic, not diagnostic labs with in-house analyzers. Revisit only if a future pilot clinic runs an in-house lab — then it's a Phase 2+ vertical integration, not core.                                                                                                                                                                                                                       |
| 6   | **Linux-style granular permissions** (read/write/delete/send, per-user or per-group, separate ruleset object) (§3.7)      | 🟡, low priority                   | kame-desk's 4 fixed roles (owner/admin/doctor/reception, `mvp.md` §6.11) plus Phase 41's per-clinic membership already cover the realistic cases for solo/small clinics. Dashlabs' finer-grained model matters more for larger multi-branch operators (e.g., a receptionist at Branch A shouldn't touch Branch B's billing). Same call as multi-branch reporting: don't build a general permission engine speculatively; revisit only if enterprise/chain clinics become a real segment.                   |
| 7   | **Result locking with authorized unlock** (§3.2)                                                                          | 🟢                                 | kame-desk's chart versioning (append-only, never overwrite, Phase 7, `mvp.md` §6.5 "Chart versioning") is a stronger guarantee than a binary lock — full audit history beats lock+unlock. No gap.                                                                                                                                                                                                                                                                                                          |
| 8   | **Admin-configurable notification trigger rules** (§3.8)                                                                  | 🟢                                 | kame-desk's Notification Center (Phase 40, done — bell UI, persisted inbox, realtime WebSocket, event catalog across schedule/clinical/billing/team) plus reminders/recalls (Phase 11) is already more sophisticated than Dashlabs' event→SMS/email rule. No gap.                                                                                                                                                                                                                                          |
| 9   | **Store Orders auto-creating the linked clinical order** (§3.3)                                                           | 🟢                                 | kame-desk's `clinical_orders` model (`mvp.md` §6.5: `ordered → in_progress → resulted/cancelled`) already separates clinical intent from billing while keeping them linked — arguably cleaner than Dashlabs' sale-creates-order coupling. No gap, just confirm the billing↔clinical_orders link stays bidirectional wherever it's implemented.                                                                                                                                                             |
| 10  | **À la carte per-module add-on pricing** (§3.11)                                                                          | Business-model note, not a feature | Not a code gap — a go-to-market pattern. Worth flagging to whoever owns Phase 30 platform monetization: if kame-desk ships new optional modules (e.g., #1's multi-station queue, or a future corporate-account package per #3), pricing them as separate add-ons rather than bundling into one flat tier is a proven pattern in this exact market.                                                                                                                                                         |
| 11  | **HMO / Charge To / APE as first-class POS payment categories** (§3.3, §3.12, §3.13)                                      | 🟡                                 | Reel: cash, HMO, Charge To, APE. Tutorial adds **E_WALLET**, **BANK**, payment-proof photo, and **per-HMO product prices** (Regular ₱500 vs HMO–Maxicare ₱350). Homepage also lists **Plans** (insurance, benefits, consumption) — not demoed. Still lighter than Agimat LOA automation, but more than kame-desk's "HMO as structured notes." Pattern to copy if we close the HMO gap: payment category + optional HMO price list on the SKU, not a lab module.                                            |
| 12  | **Package SKUs that mint clinical services** (e.g. "Basic 5") (§3.12, §3.13)                                              | 🟢 / note                          | Tutorial shows the construction: product → multiple prices → post-purchase services + variants (CBC, Chest PA). Matches sale-creates-patient-services (§3.3, §4 #9). kame-desk already has billable items + clinical orders. Keep package→order expansion if labs/APE become a segment.                                                                                                                                                                                                                    |
| 13  | **Fit-to-work / medical evaluation** (§3.5, §3.13)                                                                        | 🟡, strategic only                 | Class A–D plus a compare-all-tests evaluation screen. Occup-health/APE, not general practice SOAP. Fold into §4 #3's segment decision; do not build for solo clinics.                                                                                                                                                                                                                                                                                                                                      |
| 14  | **PhilHealth professionals settings** (§3.10, §3.13)                                                                      | 🟢 / note                          | Named homepage row only. Not e-claims, not HITP. Does **not** close `clinic-software-market-research-feature-gaps.md` §4.1 #2. Do not treat Dashlabs as the PhilHealth reference.                                                                                                                                                                                                                                                                                                                          |
| 15  | **BIR-approved computer receipts** (§3.3, §3.13)                                                                          | 🟢                                 | Dashlabs prints receipts but the cashier states the software is **not BIR approved** and that BIR math is the user's job. Confirms our prior finding: numbering format ≠ PTU/CAS/EIS. No competitive pressure to copy their receipt PDF; the compliance workstream stays ours (or the clinic's).                                                                                                                                                                                                           |

---

## 5. Where kame-desk can go further — the AI layer Dashlabs doesn't have

This is the direct answer to "we can improve and offer more AI features." **Dashlabs, despite owning the `.ai` brand in this market, ships no generative-AI features today** (§2) — no chat assistant, no drafting, no summarization, no prediction. Everything in §3 is rule-based automation (fixed routing rules, fixed permission bits, fixed notification triggers). kame-desk already has a working tiered AI Clinic Assistant (`mvp.md` §9, Phases 16/29), AI SOAP drafting + transcription (Phases 14/15), semantic chart search (Phase 15), and no-show prediction (§8.8) — real LLM infrastructure nobody else found in either this research pass or the prior competitive pass has. The opportunity is to take Dashlabs' _operational_ patterns (§4, items worth adopting) and make each one smarter than the rule-based version they shipped:

1. **If the multi-station queue (§4 #1) gets built:** don't just copy Dashlabs' static "Shortest" routing rule. Have the AI assistant predict per-station wait time from historical throughput and proactively suggest re-routing (Tier 0 read-only suggestion, front desk confirms) — dynamic instead of a fixed rule. Also expose it conversationally: "who's been waiting longest" or "which station is backed up right now" answered by the assistant instead of requiring someone to read a dashboard.

2. **If a pre-visit digital intake form (§4 #2) gets built:** match the reel's QR-at-door phone form, not only a booking-link field set. Have the assistant auto-summarize a patient's free-text intake answers into a structured pre-visit brief for the doctor before the consult starts (Tier 0, drafting only — the doctor still reads the source answers). Optionally flag self-reported symptoms that suggest urgency as a Tier 0 alert to front desk/doctor — **never a diagnosis**, respecting the existing explicit ban on AI differential-diagnosis (`mvp.md` §14). Nothing found in this research (Dashlabs or the prior competitive pass) does this.

3. **Self-serve AI-guided setup, instead of Dashlabs' white-glove onboarding:** Dashlabs' workflow builder is configured _by their own ops team_ during onboarding — a real cost center for them. If kame-desk builds a station/workflow feature (§4 #1), let the AI assistant walk a new clinic through configuring it conversationally ("we have a nurse triage station before the doctor, then billing") instead of needing a human implementation specialist. This directly undercuts a real operational cost in Dashlabs' business model, not just a feature gap.

4. **AI-assisted patient-facing result interpretation:** extend the existing AI Visit Summary pattern (`mvp.md` §8.5) to lab/test results — a plain-language explainer of what a result means, shown in the patient portal. Tier 2 (clinical content — doctor must confirm before the patient sees it), same safety pattern already used elsewhere. Dashlabs only gets results to the patient as a raw PDF certificate; nobody in this space appears to explain them.

5. **If corporate/group accounts (§4 #3) are ever pursued:** an AI copilot over aggregate corporate-account data ("how many employees from this batch were flagged for follow-up") — Tier 0, **aggregate-only**, with explicit care not to leak any individual patient's PHI to an unauthorized corporate contact (this needs its own RBAC/consent design, not just a tool wrapper).

**Positioning takeaway:** this is worth stating explicitly in kame-desk's own marketing once any of the above ships — "the only clinic platform in this market pairing real operational automation with a real AI assistant" is a defensible, verified (not assumed) claim after this research.

---

## 6. Open decisions — resolve with the user before any of §4/§5 gets scheduled

1. **Multi-station queue (§4 #1):** is this worth building for kame-desk's actual pilot clinics? It's real value for a 2–5 doctor clinic with distinct stations (nurse/vitals → doctor → billing), but it's also the largest single build in this doc. Scope check needed: start with just 2–3 stations and 2 routing types (Automatic, Manual), not Dashlabs' full 5-type flowchart engine.
2. **Pre-visit intake form (§4 #2):** the reel confirms QR-at-door phone registration that lands on the cashier screen with no re-key. Still confirm what the existing booking link/patient portal actually capture today (may already be a non-issue) before treating medical-history/consent fields as new scope.
3. **Corporate/B2B accounts (§4 #3):** does kame-desk want to expand its target segment to occupational-health/corporate-wellness clinics, or stay solo/small-practice focused per `mvp.md` §3? This is a segment decision, not an engineering one — don't build Store Ledgers/bulk pre-registration speculatively.
4. **Granular permissions (§4 #6):** same "stay simple until chains are a real segment" logic as the prior research doc's multi-branch-reporting deferral — confirm this still holds.
5. **AI enhancements (§5):** each one only makes sense contingent on its underlying feature being built first (e.g., #1 needs the multi-station queue). Sequence accordingly rather than building the AI layer ahead of the feature it enhances.
6. **Scope and sequencing:** if any of §4 gets accepted, does it become new `docs/phases/phase-XX-*.md` entries appended after Phase 47, or fold into the in-progress design-overhaul tracker? Given none of this overlaps that tracker's scope (hierarchy/density/screen redesign), it should likely be its own new phase range once decided.
7. **Video follow-up:** both requested videos are now transcribed (§3.12 reel, §3.13 Basic 5 tutorial). No remaining video gap for this research pass.

---

## 7. Suggested next step

Once §6 is resolved: convert accepted 🟡 items into new `docs/phases/phase-XX-*.md` entries following the existing phasing convention (goal, prerequisites, task checklist, data model, API surface, edge cases, testing, docs to update, exit criteria — see any Phase 33–39 file for the template), update `docs/mvp.md` §14 (Out of Scope) to reflect what's now in-scope vs. still deferred, and update `docs/architecture/ai-clinic-assistant.md`'s tool catalog for any §5 AI tools once their underlying feature is scheduled.

---

## 8. Sources

**Dashlabs.ai — video (2026-09-14 follow-up):**

- 41-second vertical clinic walkthrough MP4 (Menara Health Diagnostics / `dashlabs.app`). Whisper tiny + captions + 1 fps frames. §3.12.
- **Dashlabs Basic 5 Tutorial Video** (`OG8cdGDXiT0`, local MP4, 6:59). Whisper base + frames every 3s on Dashlabs Demo Site. §3.13.

**Dashlabs.ai — primary (highest confidence, fetched directly):**

- [dashlabs.ai](https://www.dashlabs.ai/) — homepage, positioning, target audience
- [dashlabs.ai/pricing](https://www.dashlabs.ai/pricing) — full pricing tiers and add-on list
- [dashlabs.ai/solutions/results-input-forms](https://www.dashlabs.ai/solutions/results-input-forms)
- [dashlabs.ai/solutions/online-patient-registration-form](https://www.dashlabs.ai/solutions/online-patient-registration-form)
- [help.dashlabs.ai](https://help.dashlabs.ai/) and its full documentation index at [help.dashlabs.ai/llms.txt](https://help.dashlabs.ai/llms.txt) — EMR module, Patient/Patient Service Management, Finance module, Inventory module, APE/PEME module (Site Operations, Corporate Management), Workflow & Queue, User Access Control, Notification Triggers, Result Documents, Laboratory Services, Store Orders

**Third-party (context/verification):**

- [Y Combinator — Dashlabs.ai company profile](https://www.ycombinator.com/companies/dashlabs-ai) — founding team, funding, traction, partnerships (Novartis Philippines, ICanServe Foundation)
- [BusinessWorld — "Dashlabs.ai automates lab diagnostics in clinics with AI"](https://bworldonline.com/bw-launchpad/2024/09/18/622167/dashlabs-ai-automates-lab-diagnostics-in-clinics-with-ai/) (fetch blocked by the source's own bot protection — referenced via search-result summary only, not directly read)
- Dashlabs YouTube channel: "Dashlabs Basic 5 Tutorial Video" (`OG8cdGDXiT0`, transcribed in §3.13), "Start Up #115: Dashlabs.ai," "We are Dashlabs.ai," "Simplify Healthcare with Dashlabs.ai"

**Requested video status:**

- 41-second social/reel walkthrough — **done** (§3.12).
- `https://www.youtube.com/watch?v=OG8cdGDXiT0` ("Dashlabs Basic 5 Tutorial Video") — **done** (§3.13). Local MP4 used after the YouTube page yielded no captions in pass 1.

**Internal (for the gap analysis in §4):**

- `docs/mvp.md` — §3 Target Users, §6.2–§6.15 Core Modules, §14 Out of Scope, §15 Open Questions
- `docs/phases/README.md` — phase status table
- [`docs/workflow/planned/clinic-software-market-research-feature-gaps.md`](./clinic-software-market-research-feature-gaps.md) — prior competitive research pass this doc extends
