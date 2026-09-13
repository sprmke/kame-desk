# Phase 5: Status board + WebSockets (live waiting-room queue)

**Status:** Done
**Depends on:** Phase 4
**Unlocks:** Phase 6

**mvp.md reference:** §6.4 (visit status lifecycle), §6.2 (dashboard "waiting patients"), §10 Reliability (WebSocket degrade-to-polling) · Gap closed: #4 in §7

## Goal

Introduce the **second lifecycle** — visit status (`Arrived → In Consultation → Completed`), distinct from appointment status — and a real-time waiting-room queue view driven by WebSockets, so the front desk and doctor always know who is actually physically waiting right now.

## Prerequisites

- Phase 4 done: appointments exist and are schedulable

## Tasks

### 1. Database

- [x] `visit_status_events` table (per tech-stack.md's core table list) — appointment_id, visit_status (`Arrived`/`In Consultation`/`Completed`), changed_at, changed_by_user_id. Append-only event log, not a single mutable column — the _current_ status is derivable (latest event) but history is preserved for reporting (Phase 12) and audit.
- [x] `appointments.current_visit_status` — denormalized column for fast querying, kept in sync by the same service function that inserts into `visit_status_events` (never written directly by any other code path)

### 2. Backend

- [x] `POST /api/v1/appointments/{id}/visit-status` — single service function (`transition_visit_status`) that: validates the transition is legal (no skipping backward, no re-entering `Completed`), inserts the event row, updates the denormalized column, writes `activity_log`, and broadcasts a WebSocket event — **all side effects live here, never duplicated in a route handler** (per `CLAUDE.md` Don'ts)
- [x] `GET /api/v1/appointments/waiting-room` — today's appointments with current visit status, for the initial page load (WebSocket only pushes deltas after that)
- [x] `WS /ws/clinic/{clinic_id}` — authenticated WebSocket endpoint, broadcasts `appointment.visit_status_changed`, `appointment.created`, `appointment.rescheduled`, `appointment.cancelled` events to all connected clients in that clinic
- [x] Server-side connection management: track connections per clinic, clean up on disconnect, re-check auth/clinic-membership on connect (not just on the initial HTTP handshake if the token can expire mid-session — handle token refresh over the socket or force reconnect)

### 3. Frontend

- [x] `src/lib/websocket.ts` — connection manager with automatic reconnect + exponential backoff
- [x] **Polling fallback**: if the WebSocket connection fails or drops repeatedly, fall back to polling `GET /waiting-room` every N seconds — per mvp.md §10, "front desk must never be blind to patient status because of a dropped socket." Surface a subtle "reconnecting" indicator, never a silent failure.
- [x] On receipt of a WS event, invalidate the relevant TanStack Query cache key rather than manually patching state (per tech-stack.md's realtime pattern: "WebSocket client → TanStack Query invalidation")
- [x] `src/features/waiting-room/` — kanban-style or list-style board: Scheduled → Arrived → In Consultation → Completed columns, one-tap status advance buttons sized for tablet (44×44px)
- [x] Dashboard "waiting patients" widget wired to the same live data

## Data model

New: `visit_status_events`. Extended: `appointments.current_visit_status`.

## API endpoints

| Method | Path                                     | Roles                           |
| ------ | ---------------------------------------- | ------------------------------- |
| POST   | `/api/v1/appointments/{id}/visit-status` | owner, admin, doctor, reception |
| GET    | `/api/v1/appointments/waiting-room`      | owner, admin, doctor, reception |
| WS     | `/ws/clinic/{clinic_id}`                 | any authenticated clinic member |

## Edge cases & safety

- A dropped WebSocket must degrade to polling automatically and reconnect automatically when the network recovers — write an explicit test/manual-QA step for this, it's a named non-functional requirement (§10).
- Visit status transitions must be idempotent from the client's perspective (double-tapping "Mark Arrived" must not create two events or error visibly).
- A `Cancelled`/`No Show`/`Rescheduled` appointment status (Phase 3/4) must not be advanceable through visit status — the two lifecycles interact (an appointment cancelled after the patient already arrived is an edge case to define explicitly: does the visit stay in the queue? Recommend: no, cancelling always removes from the active queue, log the transition).
- Multiple staff tablets updating the same patient's status concurrently: last-write-wins is acceptable here (unlike the appointment exclusion constraint), but the event log means nothing is silently lost — both events are recorded.

## Testing

- [x] pytest: valid/invalid visit status transitions, WebSocket broadcast fires on transition, `activity_log` row written
- [x] Vitest/integration: reconnect logic, polling fallback trigger condition
- [x] Manual QA checklist item added to `docs/phases/phase-19-hardening-production-readiness.md`: kill the WebSocket mid-session, confirm the UI degrades gracefully

## Docs to update in this phase

- [x] `.cursor/rules/appointment-workflow.mdc` — document the visit-status state machine alongside the appointment-status one, and the interaction rule between them
- [x] `docs/architecture/data-model.md` — `visit_status_events`
- [x] `docs/guides/routes/dashboard/waiting-room.md`

## Exit criteria

- [x] Real-time queue updates across multiple simultaneous clients (test with 2+ browser tabs)
- [x] WebSocket drop → automatic polling fallback → automatic reconnect, verified manually
- [x] Visit status history is fully auditable via `visit_status_events`
- [x] `pnpm run ci:quality` green
