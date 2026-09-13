# DoctorDesk — build plan (phases)

This is the **execution plan** for building DoctorDesk from an empty `apps/` tree to the production-ready MVP defined in [`../mvp.md`](../mvp.md). It sequences every module in that PRD, plus the AI Clinic Assistant (§9), into buildable, independently-shippable phases.

**How to use this**

- Read [`../mvp.md`](../mvp.md) and [`../tech-stack.md`](../tech-stack.md) first — this plan does not redefine scope or stack, it sequences them.
- Work **one phase at a time, in order**. Do not start phase N+1 until phase N's exit criteria are checked off.
- Each phase file is self-contained: goal, prerequisites, detailed task checklist (backend/frontend/database/AI-tooling), data model touched, API surface, edge cases, testing, docs to update, and exit criteria.
- When a phase's tasks change scope during implementation, edit that phase file in the same change — this plan is a living document, not a one-time artifact.
- Every phase ends with the same non-negotiable step: run `pnpm run ci:quality`, update the docs this repo requires (see each phase's "Docs to update"), and flip its status below before moving on.

**Numbering matches [`mvp.md` §13 Build Order](../mvp.md#13-build-order--phasing) exactly, item for item**, with one addition: **Phase 0**, which does not exist in the PRD because it produces the AI agent tooling used to build every other phase, not product scope.

## Status table

| #   | Phase                                                                                                    | Status      | Depends on |
| --- | -------------------------------------------------------------------------------------------------------- | ----------- | ---------- |
| 0   | [AI tooling & agent setup](./phase-00-ai-tooling-and-agent-setup.md)                                     | Done        | —          |
| 1   | [Monorepo scaffold, Docker Compose, auth, roles](./phase-01-monorepo-scaffold.md)                        | Done        | 0          |
| 2   | [Clinic onboarding wizard + multi-doctor support](./phase-02-onboarding-multi-doctor.md)                 | Done        | 1          |
| 3   | [Patients + appointments + exclusion constraint](./phase-03-patients-appointments.md)                    | Done        | 2          |
| 4   | [Day calendar, drag reschedule, public self-service booking link](./phase-04-calendar-public-booking.md) | Done        | 3          |
| 5   | [Status board + WebSockets (live waiting-room queue)](./phase-05-status-board-websockets.md)             | Done        | 4          |
| 6   | [Walk-in, reschedule, no-show, recurring series](./phase-06-walkin-recurring.md)                         | Done        | 5          |
| 7   | [SOAP versions, vitals, follow-up, specialty templates](./phase-07-soap-vitals-templates.md)             | Done        | 6          |
| 8   | [Prescriptions (e-Rx)](./phase-08-prescriptions.md)                                                      | Done        | 7          |
| 9   | [Billing & payments](./phase-09-billing-payments.md)                                                     | Done        | 8          |
| 10  | [Document generation](./phase-10-document-generation.md)                                                 | Done        | 9          |
| 11  | [Reminders + recall campaigns](./phase-11-reminders-recalls.md)                                          | Done        | 10         |
| 12  | [Reports & analytics](./phase-12-reports-analytics.md)                                                   | Done        | 11         |
| 13  | [Audit log surfaced in UI](./phase-13-audit-log-ui.md)                                                   | Done        | 12         |
| 14  | [PydanticAI SOAP draft + SSE streaming](./phase-14-ai-soap-draft-sse.md)                                 | Done        | 13         |
| 15  | [Transcription + pgvector chart search](./phase-15-transcription-chart-search.md)                        | Done        | 14         |
| 16  | [AI Clinic Assistant v1 (Tier 0 → Tier 1 → Tier 2)](./phase-16-ai-clinic-assistant-v1.md)                | Done        | 15         |
| 17  | [AI safety checks on prescriptions + AI billing/receipt assist](./phase-17-ai-safety-billing-assist.md)  | Done        | 16         |
| 18  | [Patient-facing booking/FAQ assistant + AI visit summaries](./phase-18-patient-facing-assistant.md)      | Done        | 17         |
| 19  | [Hardening pass + full production readiness checklist](./phase-19-hardening-production-readiness.md)     | Done        | 18         |
| 20  | [Trust repairs (LLM assistants, SMS, visit summary, document gate)](./phase-20-trust-repairs.md)         | Done        | 19         |
| 21  | [Account & session foundations](./phase-21-account-session-foundations.md)                               | Done        | 20         |
| 22  | [Settings that actually reach production](./phase-22-settings-production.md)                             | Done        | 21         |
| 23  | [Patient record integrity](./phase-23-patient-record-integrity.md)                                       | Done        | 22         |
| 24  | [Scheduling & booking that scales past one doctor](./phase-24-scheduling-booking.md)                     | Done        | 23         |
| 25  | [Clinical safety and specialty depth](./phase-25-clinical-safety.md)                                     | Done        | 24         |
| 26  | [Billing integrity](./phase-26-billing-integrity.md)                                                     | Done        | 25         |
| 27  | [Communications you can trust](./phase-27-communications.md)                                             | Done        | 26         |
| 28  | [Reports and audit that non-engineers can use](./phase-28-reports-audit.md)                              | Done        | 27         |
| 29  | [AI Clinic Assistant v2](./phase-29-ai-assistant-v2.md)                                                  | Done        | 20, 28     |
| 30  | [Platform layer: Super Admin, tenancy, and monetization](./phase-30-platform-super-admin.md)             | Done        | 21         |
| 31  | [Mobile, PWA, and design-system consolidation](./phase-31-mobile-pwa-design-system.md)                   | Done        | 26         |
| 32  | [Production readiness closeout](./phase-32-production-readiness.md)                                      | Done        | 29, 30, 31 |
| 33  | [PH payer workflow: HMO eligibility, LOA, PhilHealth e-claims path](./phase-33-ph-payer-workflow.md)     | Done        | 26         |
| 34  | [BIR compliance depth](./phase-34-bir-compliance-depth.md)                                               | Done        | 26         |
| 35  | [WhatsApp/Messenger/Viber messaging channel](./phase-35-messaging-channels.md)                           | Done        | 27         |
| 36  | [Offline / degraded-connectivity resilience](./phase-36-offline-resilience.md)                           | Done        | 31         |
| 37  | [Patient self-service portal](./phase-37-patient-portal.md)                                              | Done        | 21, 24     |
| 38  | [Growth & retention differentiators](./phase-38-growth-retention-features.md)                            | Done        | 26, 27     |
| 39  | [Interactive odontogram / dental charting module](./phase-39-dental-odontogram.md)                       | Done        | 7          |
| 40  | [In-app Notification Center (staff alerts)](./phase-40-in-app-notifications.md)                          | Done        | 5, 11      |
| 41  | [Multi-clinic organizations (org envelope)](./phase-41-multi-clinic-organizations.md)                    | Done        | 30, 21     |
| 42  | [Design System Pilot & Waiting Room Overhaul](./phase-42-design-system-pilot.md)                         | Done        | 31, 41     |
| 43  | [Anti-slop rules, design-review skill, screenshot harness](./phase-43-anti-slop-rules-harness.md)        | Done        | 42         |
| 44  | [Hierarchy and density system (end card soup)](./phase-44-hierarchy-density.md)                          | Not started | 42, 43     |
| 45  | Screen redesign: shell, entry, Today, Schedule, Waiting room                                             | Not started | 44         |
| 46  | Screen redesign: Patients, Clinical, Billing, Documents, Insights, Settings, Assistant                   | Not started | 44         |
| 47  | Native mobile feel + accessibility gates                                                                 | Not started | 45, 46     |

Phases 20–32: [`docs/workflow/planned/ground-up-app-redesign-and-platform-admin.md`](../workflow/planned/ground-up-app-redesign-and-platform-admin.md). Phases 33–39: [`docs/workflow/planned/clinic-software-market-research-feature-gaps.md`](../workflow/planned/clinic-software-market-research-feature-gaps.md). Phases 40–41: [`docs/workflow/planned/in-app-notifications.md`](../workflow/planned/in-app-notifications.md), [`docs/workflow/planned/multi-clinic-organizations.md`](../workflow/planned/multi-clinic-organizations.md). Phases 42–47: [`docs/workflow/planned/professional-design-overhaul-anti-slop.md`](../workflow/planned/professional-design-overhaul-anti-slop.md) (tracker: [`docs/workflow/in-progress/professional-design-overhaul-anti-slop.md`](../workflow/in-progress/professional-design-overhaul-anti-slop.md)). Write a full phase file before coding each one. Phase files for 45–47 do not exist yet.

Status values: `Not started` → `In progress` → `Blocked (<reason>)` → `Done`. Update this table in the same commit that changes a phase's status.

## Cross-cutting rules that apply to every phase

These are not repeated in full in every phase file — read them once, they govern all work:

1. **Docs are the source of truth** — see `CLAUDE.md` § Docs are the source of truth. Every phase's "Docs to update" section is the minimum; if a phase touches something not listed there (a new env var, a new route), update the matching doc anyway.
2. **RBAC is re-checked server-side on every endpoint** — never rely on the UI hiding a button. See `docs/architecture/security-compliance.md`.
3. **Multi-doctor / clinic scoping from day one** — every table that isn't global carries `clinic_id`; every query is scoped through the authenticated user's clinic membership. Never trust a client-supplied `clinic_id`. See `docs/architecture/data-model.md`.
4. **No business logic in `apps/web`** — TanStack Start owns UI only; FastAPI owns all business logic, including anything that looks like a "server function" shortcut.
5. **AI output is always a draft a human confirms** — no phase ships an AI feature that writes clinical, financial, or patient-facing data without an explicit human confirm step. See `docs/architecture/ai-clinic-assistant.md`.
6. **Alembic migrations are additive** — never edit a shipped migration under `apps/api/migrations/versions/`; add a new one.
7. **PHI/PII safety** — never log patient content in plaintext, never send it to Sentry payloads, never pass more patient data into an AI prompt/tool call than that call strictly needs.
8. **Every phase ships with `pnpm run ci:quality` green** (lint, type-check, build, tests) before being marked Done — this is the same gate CI runs.
9. **Mobile/tablet usability is not optional** — every screen shipped in any phase must work at 375–1024px+ with 44×44px touch targets before that phase is marked Done.
10. **Every mutating capability emits an `activity_log` row** (or documents why not) — the table exists from Phase 1 onward; there is no phase after that where this is optional.

## Relationship to other docs

| Doc                                      | Role                                                                                                                                                                                                   |
| ---------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| [`../mvp.md`](../mvp.md)                 | Authoritative PRD — what ships, and why. This plan sequences it, never contradicts it.                                                                                                                 |
| [`../tech-stack.md`](../tech-stack.md)   | Authoritative technology choices — this plan follows it, never redefines it.                                                                                                                           |
| [`../architecture/`](../architecture/)   | Standing architecture reference (monorepo structure, data model, API conventions, AI assistant spec, deployment, security) — read the relevant file before starting a phase that touches that surface. |
| [`../guides/routes/`](../guides/routes/) | Per-page behavior spec, created starting Phase 1 (directory + index), populated as each phase ships a real route (see `.cursor/rules/route-guides.mdc`).                                               |
| `CLAUDE.md`                              | Always-loaded agent context — stack, commands, conventions, don'ts. Kept in sync as phases land real paths/commands.                                                                                   |

## Out of scope for this plan

Anything in [`mvp.md` §14 "Out of Scope for MVP (Phase 2+)"](../mvp.md#14-out-of-scope-for-mvp-phase-2) has no phase file here on purpose. Do not add one without first updating `mvp.md` to move the item into scope.
