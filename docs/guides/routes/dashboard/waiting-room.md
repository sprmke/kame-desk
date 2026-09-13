# Waiting room (`/dashboard/waiting-room`)

**Status:** Documented

## Overview

- Live operational queue for today's visits: Scheduled, Arrived, In consultation, Completed. Updates via WebSocket (`RealtimeProvider` in `DashboardShell`) with polling fallback when the socket drops.
- **Workflow & UI/UX (Canonical Drag-and-Drop Kanban):**
  - **Desktop (`lg+`):** Four-column interactive board with drag-and-drop (`KanbanBoard` / `@dnd-kit`). Staff can drag patient cards between columns (`Scheduled` → `Arrived` → `In consultation` → `Completed`) or use the one-tap forward action button on each card. Invalid skips or backward transitions are rejected. Walk-in is opened via the top action button.
  - **Phone/tablet (`<lg`):** Segmented column switcher (`Scheduled`, `Arrived`, `In consult`, `Done`) with vertical list. An empty column uses a card. Staff can swipe a card left to reveal the forward action, or tap the action button directly. Walk-in opens a native bottom sheet (`ResponsiveModal`).
- **Elapsed wait badges:** Cards in Arrived and In consultation show a live wait duration (`14m wait`, `1h 5m wait`) with `tabular-nums`, updating every 15 seconds. Urgency: green under 15m, outline 15–29m, amber warning at 30m+. Arrived column sorts longest wait first. Cards show initials plus the patient name.
- **Doctor filter:** When two or more doctors appear in today's queue, filter pills (`All`, each doctor + count) sit above the board. Choice persists in `localStorage` (`dd-waiting-room-doctor`).
- **Arrival feedback:** Remote `visit.arrived` notifications already toast via the Notification Center. A soft two-tone chime plays with that toast unless reduced motion is on or `localStorage` `dd-waiting-room-chime=off`. The actor who marked Arrived does not hear their own toast/chime.

## Behavior

- Loads today's non-terminal appointments (`GET /api/v1/appointments/waiting-room`).
- Dashboard home (`/dashboard`) shows a Queue card of the same live waiting-room data. When the queue is empty, the board shows a compact empty state.
- One-tap buttons advance visit status forward only (`Arrived` → `In Consultation` → `Completed`). Idempotent re-tap on the same status succeeds silently.
- Desktop drag-and-drop calls the same `POST visit-status` endpoint as the button. Only the next forward transition is accepted; dropping on Scheduled or skipping a step does nothing.
- Cancelled / No Show / Rescheduled appointments are excluded from the queue and cannot receive visit status updates.
- Completed visits show a visit summary card: edit, **Send**, or **Suppress**. If AI generation failed, the card says so and Send stays disabled until the doctor types a summary. Summaries never send without explicit approval.

## Save paths

| UI action         | API                                           | DB effect                                                                                    |
| ----------------- | --------------------------------------------- | -------------------------------------------------------------------------------------------- |
| Tap status button | `POST /api/v1/appointments/{id}/visit-status` | Insert `visit_status_events`, update `appointments.current_visit_status`, `activity_log` row |
| Drag to column    | Same as tap (when transition is valid)        | Same                                                                                         |
| WS event received | (client invalidates TanStack Query)           | Refetch waiting room                                                                         |

activity-log: N/A — wait badges, doctor filter, and arrival chime are presentation-only; visit status writes still go through `visit_service` / existing `visit.status_changed` + `notify_visit_status`.

## Validation

- Illegal backward or skip transitions return 400.
- Terminal appointment status blocks visit updates (400).

## RBAC

`owner`, `admin`, `doctor`, `reception` (clinic staff via JWT + `X-Clinic-Id`).

## AI assistant parity

No assistant tool in Phase 5. Visit transitions are Tier 2 when added in Phase 16.

## Edge cases

- Concurrent tablets: last write wins on denormalized column; both events remain in `visit_status_events`.
- Socket drop: client polls every 5s and keeps reconnecting with exponential backoff.
- Drag while a status update is in flight is disabled until the request finishes.
- Doctor filter with a saved id that is no longer in today's queue falls back to All.
- Arrival chime is skipped when `prefers-reduced-motion: reduce` or when browsers block AudioContext.

## Implementation map

- Web: `apps/web/src/features/waiting-room/` (`WaitingRoomKanban.tsx`, `WaitingRoomBoard.tsx`, `DoctorFilterBar.tsx`, `lib/waitTime.ts`, `lib/arrivalChime.ts`), `components/ui/kanban-board.tsx`, route `apps/web/src/routes/dashboard.waiting-room.tsx`, `apps/web/src/lib/websocket.ts`, chime hook in `features/notifications/lib/NotificationToast.tsx`
- API: `apps/api/app/services/visit_service.py`, `apps/api/app/routers/appointments.py`, `apps/api/app/routers/ws.py`

## Host-facing knowledge

The waiting room shows who is physically at the clinic today. Move a patient to **Arrived** when they check in, **In consultation** when the doctor sees them, and **Completed** when they leave. Wait time on Arrived cards updates live; longer waits sort to the top. If more than one doctor is seeing patients today, use the doctor pills above the board to filter. On a phone, tap the status button or swipe a card left and tap the revealed action. On a desktop, drag a card to the next column or use the button. Open **Walk-in** from the top of the screen. If another staff member checks someone in, you get a toast (and a soft chime) with the patient name. If the live indicator shows Polling, the screen still refreshes every few seconds. After a visit is completed, a visit summary card appears for the doctor: edit if needed, then Send or Suppress. If AI could not write a draft, write one yourself before Send.

**Q: A patient was cancelled but still shows on the board?**  
A: Refresh the page. Cancelled appointments should drop from the queue immediately; if one remains, check that the appointment status is actually Cancelled.

**Q: Can we move a patient back to Arrived?**  
A: No. Visit status only moves forward for the day.

**Q: Can I drag a card straight to Completed?**  
A: No. Cards only move one step at a time, same as the status button.

**Q: How do I see only Dr. Santos's queue?**  
A: Tap the doctor pill above the board. Tap **All** to clear the filter.
