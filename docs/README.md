# DoctorDesk docs

Documentation for **DoctorDesk** (kame-desk): clinic desk software for a **one-doctor + secretary** practice (calendar, waiting room, SOAP, Rx, billing/HMO).

## Index

| Doc                                       | Description                                                                                                                                             |
| ----------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [mvp.md](./mvp.md)                        | **Authoritative MVP PRD** (v1.2 solo-clinic) — 1 doctor + secretary, keep/cut list, AI assistant, HMO billing                                           |
| [tech-stack.md](./tech-stack.md)          | Final recommended stack: frontend, backend, data, hosting, AI, and what we explicitly skip                                                              |
| [phases/README.md](./phases/README.md)    | **Multi-phase build plan** — Phases 0–47, detailed tasks/data model/API/edge cases/exit criteria each                                                   |
| [architecture/](./architecture/)          | Standing architecture reference: monorepo structure, data model, API conventions, AI assistant spec, design language, deployment, security & compliance |
| [guides/routes/](./guides/routes/)        | Per-page behavior guides, created starting Phase 1, populated as each phase ships a real route                                                          |
| [workflow/](./workflow/planned/README.md) | Plans and execution trackers (`planned/`, `in-progress/`, `done/`)                                                                                      |

## Current status

**Phases 0–43 Done.** Product scope is the **solo-clinic MVP** ([`mvp.md`](./mvp.md) v1.2): one doctor + secretary. Multi-doctor clinics are Phase 2 (APIs stay; clinic UI is hidden). Active visual work is the professional design overhaul (Phases 42–47) on **kept** screens only. Phase 42 and 43 are shipped. Next is **Phase 44**. Tracker: [`workflow/in-progress/professional-design-overhaul-anti-slop.md`](./workflow/in-progress/professional-design-overhaul-anti-slop.md). Operational `mvp.md` §12 gates stay open on purpose.

## Product scope (v1.2)

See [mvp.md](./mvp.md) for the full, authoritative scope. Summary:

- **Users:** one doctor (owner) and one secretary (reception). Dentist, pedia, OB-GYN, family/internal med, ENT.
- Appointment lifecycle: Scheduled, Confirmed, Cancelled, No Show, Rescheduled. Day-of: Arrived, In Consultation, Completed
- One-doctor calendar, walk-ins, optional recurring, double-booking prevention, optional public booking link (slot picker, no patient chatbot)
- Patients, SOAP (versioned, specialty templates including dental odontogram), prescriptions, invoices + HMO claims/eligibility/LOA, certificates/referrals, email reminders, simple reports, roles & audit log
- AI SOAP draft (doctor confirms) and **AI Clinic Assistant** (book, look up, draft notes, billing/HMO) with a tiered risk model
- **Phase 2 (hidden):** multi-doctor calendars, rooms, waitlist, org/add-clinic, patient portal, recall campaigns, WhatsApp, memberships, BIR PTU/CAS UI

## Repo layout

```
kame-desk/
├── apps/
│   ├── web/          # React + TanStack Start + Vite
│   └── api/          # FastAPI
├── packages/
│   └── api-client/   # OpenAPI-generated TypeScript client
├── docs/
└── docker-compose.yml
```

See [tech-stack.md](./tech-stack.md) for authoritative technology choices.
