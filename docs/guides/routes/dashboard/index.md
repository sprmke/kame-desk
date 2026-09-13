# Dashboard (`/dashboard`)

**Status:** Documented

## Progress overview

| Section          | E2E | Validation | Docs | Notes                                          |
| ---------------- | --- | ---------- | ---- | ---------------------------------------------- |
| KPI cards        | N/A | N/A        | Done | Today, Waiting, Completed, Revenue             |
| Today + queue    | N/A | N/A        | Done | Queue owns floor visits; Today omits them      |
| Trend + upcoming | N/A | N/A        | Done | 14-day chart and next 7 days                   |
| Follow-up cards  | N/A | Partial    | Done | Outstanding, Recalls, Failed reminders, Claims |

## Overview

Home screen for clinic staff after sign-in. It answers what is happening today and what still needs follow-up (queue, balances, recalls, failed reminders, open claims). On a phone, open Dashboard from **More**.

## Host-facing knowledge

The dashboard is the morning board. Four number cards show **Today**, **Waiting**, **Completed**, and **Revenue**. **Today** is this clinic day's appointments that are not already in the waiting room. **Queue** is who has arrived or is with the doctor. **Waiting** is that same floor count. A "scheduled" hint under Waiting means people are booked but have not arrived yet; they stay on Today, not Queue. **Completed** is finished visits. **Revenue** is payments this month, with today and this week underneath. The highlighted row in Today is the next slot. Queue stays live while the indicator says Live; Polling still refreshes every few seconds. **Appointments, last 14 days** is booked vs completed. **Upcoming** is the next 7 days. Four follow-up cards cover outstanding balances, recalls, failed reminders, and open claims. Walk-in, New patient, and New appointment are on the top of the page. The assistant launcher stays in the corner on every dashboard screen.

**Q: Why is the next patient highlighted?**
A: That row is the next uncompleted appointment from now. It is not a status change.

**Q: I do not see Recalls.**
A: Recalls are for owner, admin, and reception. Doctors still see Today, Queue, Upcoming, billing, reminders, and claims.

**Q: I do not see the 14-day chart.**
A: That chart is for owner and admin. Open Insights → Reports for the full appointments report. Doctors and reception see Calendar and Upcoming instead.

**Q: Retry on a failed reminder did nothing.**
A: Retry only works on failed rows. Open Reminders if it still fails after a second try.

## Behavior

- Quick actions: **New appointment**, **Walk-in** (`WalkInDialog` / `ResponsiveModal`), **New patient**.
- KPI cards (Today, Waiting, Completed, Revenue) open Appointments, Waiting room, and Invoices.
- **Today** lists this Manila calendar day's appointments that are not Arrived or In consultation (those belong on Queue). Rows open the SOAP note.
- **Queue** lists who has Arrived or is In consultation, with the live/polling indicator. Booked-but-not-arrived visits stay on Today. Updates share the clinic WebSocket used on `/dashboard/waiting-room`.
- **Appointments, last 14 days** is booked vs completed (`GET /reports/appointments`). All opens Insights → Reports.
- **Upcoming** lists the next 7 days in one column beside the chart (time, then name). Extra days scroll inside the card. Next to Calendar it uses a two-column week strip.
- **Outstanding**, **Recalls**, **Failed reminders**, and **Claims** are separate cards. Failed reminder rows can Retry. Claim rows open that claim.
- Today, Queue, the 14-day chart, Upcoming, and follow-up modules sit in bordered cards with a stable body height. Extra rows scroll inside the card.

## Save paths

Read-only except walk-in and reminder retry.

| UI action      | API                                                                                                                                                                                                                                           | DB effect                                             |
| -------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------- |
| Load home      | `GET /appointments`, `GET /appointments/waiting-room`, `GET /clinics/{id}/revenue-summary`, `GET /clinics/{id}/outstanding-balances`, `GET /clinics/{id}/recalls`, `GET /reminders?status=failed`, `GET /claims`, `GET /reports/appointments` | none                                                  |
| Walk-in        | `POST /appointments/walk-in`                                                                                                                                                                                                                  | appointment + `activity_log` (`appointment.walk_in`)  |
| Retry reminder | `POST /reminders/{id}/retry`                                                                                                                                                                                                                  | reminder resend + `activity_log` (`reminder.retried`) |

activity-log: N/A for the dashboard itself (no new writes). Walk-in and retry already log in their services.

## RBAC

All clinic staff can open `/dashboard`. Server RBAC still applies per endpoint:

| Widget                                                          | Roles                                       |
| --------------------------------------------------------------- | ------------------------------------------- |
| Today, queue, upcoming, reminders, claims, outstanding, revenue | clinic staff (billing reads include doctor) |
| 14-day appointments chart                                       | `reports:view` (owner, admin)               |
| Recalls                                                         | owner, admin, reception                     |

## AI assistant parity

No dashboard-specific tools. The floating assistant launcher is unchanged (`docs/architecture/ai-clinic-assistant.md`).

## Edge cases

- Manila calendar dates (`Asia/Manila`) for "today" and upcoming, not the browser's local zone.
- Cancelled / No Show / Rescheduled appointments are excluded from KPI counts and calendar dots; they still appear on Today so the desk can see them.
- If the appointments list fails, the page shows Retry. Other cards load on their own.
- Realtime is mounted for every `/dashboard/*` screen so the waiting-room indicator is accurate outside the queue page.

## Implementation map

- Web: `apps/web/src/features/dashboard/pages/DashboardOverviewPage.tsx`, `apps/web/src/features/dashboard/components/`, `apps/web/src/features/dashboard/lib/`
- Shell realtime: `DashboardShell` + `RealtimeProvider`
- Route: `apps/web/src/routes/dashboard.index.tsx`

## Related docs

- [Waiting room](./waiting-room.md)
- [Billing invoices](./billing/invoices.md)
- [Recalls](./recalls.md)
- [Reminders](./reminders.md)
- [Reports](./reports.md)
- [Claims](./billing/claims.md)
- [Eligibility checks](./billing/eligibility.md)
- [LOA requests](./billing/loa.md)
