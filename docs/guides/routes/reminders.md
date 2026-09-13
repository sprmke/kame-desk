# Public reminder reply (`/reminders/{token}`)

**Status:** Documented

## Behavior

- Token-scoped page (no auth). Actions: confirm appointment, cancel, or request reschedule (logs staff-visible activity).
- Invalid or expired tokens return 404.
- The same reply_token also resolves confirm/cancel when a patient taps the quick-reply button on a WhatsApp reminder (Phase 35) — the WhatsApp inbound webhook (`app/routers/whatsapp_webhook.py`) calls the same underlying `respond_to_reminder()` service function as this page, so both entry points behave identically. Reschedule-request has no WhatsApp equivalent (button replies only carry confirm/cancel).

## Save paths

| Action             | API                                      | Effect                                      |
| ------------------ | ---------------------------------------- | ------------------------------------------- |
| Confirm            | `POST /public/reminders/{token}/respond` | appointment status → Confirmed when allowed |
| Cancel             | same                                     | appointment status → Cancelled              |
| Reschedule request | same, `action: reschedule_request`       | `activity_log` only; staff follows up       |

## RBAC

None (token is the scope).

## Implementation map

- Web: `apps/web/src/routes/reminders.$token.tsx`
- API: `apps/api/app/routers/public_reminders.py`, `apps/api/app/services/reminder_service.py` (`respond_to_reminder`)

## Host-facing knowledge

Reminder emails include a link patients can use without logging in. Confirm moves the appointment to Confirmed. Cancel cancels the visit. Request reschedule notifies the clinic to call the patient back.
