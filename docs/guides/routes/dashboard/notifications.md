# Staff alerts (`/dashboard/notifications`)

**Status:** Documented

Not the same as `/dashboard/settings/notifications` (patient email/SMS/WhatsApp reminder prefs).

## Behavior

- Clinic-scoped inbox for operational events (bookings, visit flow, billing, messaging, team). The list uses the same full page width as other dashboard pages.
- Per-user read state; marking read does not affect other staff.
- The page header describes the purpose of alerts. Filter and "Mark all read" actions are hidden when there are no alerts. The empty state explains what will appear here.
- Bell in the header (`AppHeader`) shows unread count (capped at 99+). Only the count query runs on page load; the list is fetched when the panel opens. Popover on `lg+`, bottom sheet below.
- Realtime: `notification.created` / `notification.updated` on the clinic WebSocket; falls back to polling when the socket degrades.
- Toasts via Sonner; the actor who triggered an action does not get a toast for that row.
- Optional Web Push when `VAPID_*` env vars are set (`Push alerts` on the Alerts page).

## Save paths

| Action        | API                                      | DB                                        |
| ------------- | ---------------------------------------- | ----------------------------------------- |
| List          | `GET /api/v1/notifications`              | `notifications` + reads                   |
| Unread count  | `GET /api/v1/notifications/unread-count` | derived                                   |
| Mark one read | `POST /api/v1/notifications/{id}/read`   | `notification_reads` insert               |
| Mark all      | `POST /api/v1/notifications/read-all`    | bulk reads                                |
| Mute type     | `PATCH /api/v1/notifications/prefs`      | `in_app_notification_prefs` on membership |

Event inserts always go through `notification_service.create_notification` from domain services after the primary write commits.

## RBAC

Any active clinic member sees rows whose audience matches their role (or targeted user/doctor). No separate `notifications:view` permission.

## Host-facing knowledge

- **What is this?** A front-desk and doctor alert feed for things that need attention now or later (online booking, patient arrived, payment posted, reminder failed).
- **Where is it?** Bell icon top-right. Tap **View all** in that panel for the full list.
- **Settings vs alerts?** Settings → Notifications controls messages **to patients**. Alerts are **for staff inside the app**.

## Implementation map

- Web: `apps/web/src/features/notifications/`, route `dashboard.notifications.tsx`
- API: `apps/api/app/services/notification_service.py`, `routers/notifications.py`
