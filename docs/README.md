# DoctorDesk docs

Documentation for **DoctorDesk** (kame-desk): clinic desk software for scheduling, live visit status, and SOAP consultation records.

## Index

| Doc                                       | Description                                                                                                                                             |
| ----------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [mvp.md](./mvp.md)                        | **Authoritative MVP PRD** — goals, full module list, AI Clinic Assistant spec, production readiness checklist                                           |
| [tech-stack.md](./tech-stack.md)          | Final recommended stack: frontend, backend, data, hosting, AI, and what we explicitly skip                                                              |
| [phases/README.md](./phases/README.md)    | **Multi-phase build plan** — Phases 0–47, detailed tasks/data model/API/edge cases/exit criteria each                                                   |
| [architecture/](./architecture/)          | Standing architecture reference: monorepo structure, data model, API conventions, AI assistant spec, design language, deployment, security & compliance |
| [guides/routes/](./guides/routes/)        | Per-page behavior guides, created starting Phase 1, populated as each phase ships a real route                                                          |
| [workflow/](./workflow/planned/README.md) | Plans and execution trackers (`planned/`, `in-progress/`, `done/`)                                                                                      |

## Current status

**Phases 0–43 Done.** Active work is the professional design overhaul (Phases 42–47). Phase 42 (waiting-room pilot) and Phase 43 (anti-slop enforcement) are shipped. Next is **Phase 44** (hierarchy and density). Tracker: [`workflow/in-progress/professional-design-overhaul-anti-slop.md`](./workflow/in-progress/professional-design-overhaul-anti-slop.md). Brand hue is still open; next visual pilot is Today (`/dashboard`). Operational `mvp.md` §12 gates stay open on purpose. Start at [`phases/README.md`](./phases/README.md) for the full build order.

## Product scope (v1)

See [mvp.md](./mvp.md) for the full, authoritative scope. Summary:

- Appointment lifecycle: Scheduled, Confirmed, Cancelled, No Show, Rescheduled. Day-of visit lifecycle: Arrived, In Consultation, Completed
- Drag-and-drop scheduling, walk-ins, recurring appointments, double-booking prevention, public self-service booking link
- Color-coded appointments
- Patients, prescriptions, billing & payments, document generation (certificates/referrals), reminders/recalls, reports, roles & audit log
- SOAP EMR: Subjective, Objective, Assessment, Plan, plus diagnosis, vitals, treatment plan, follow-up date, chart versioning, specialty templates
- AI assist (draft SOAP, transcription, chart search) with doctor confirmation before save
- **AI Clinic Assistant**: chat-driven, tool-calling dashboard assistant (tiered risk model, RBAC-scoped, full audit trail) so staff can book/reschedule/bill/draft notes by asking instead of clicking

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
