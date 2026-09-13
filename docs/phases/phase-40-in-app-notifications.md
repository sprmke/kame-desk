# Phase 40: In-app Notification Center

**Status:** Done
**Depends on:** Phase 5, Phase 11

## Goal

Staff inbox: persisted alerts, bell badge, Sonner toasts, mark-read, Redis fan-out to clinic WebSocket, optional Web Push.

## Prerequisites

- Phase 5 WebSocket waiting-room channel
- Phase 11 patient reminder settings (separate from staff alerts)

## Backend

- [x] Migration `035_in_app_notifications` — `notifications`, `notification_reads`, `push_subscriptions`, `clinic_memberships.in_app_notification_prefs`
- [x] `notification_service.create_notification` (non-fatal, dedupe, coalesce for WhatsApp)
- [x] REST: `GET /notifications`, unread count, mark read, mark all, prefs, push subscribe
- [x] Redis pub/sub → `/ws/clinic/{id}` events `notification.created` / `notification.updated`
- [x] Emit helpers wired across schedule, clinical, billing, messaging, team, security services
- [x] ARQ retention cron `purge_old_notifications_job` (90 days)

## Frontend

- [x] `NotificationBell` in header; `/dashboard/notifications` Alerts page
- [x] Extend `ClinicRealtimeClient` for notification events + polling fallback
- [x] Sonner toasts; suppress toast for `actor_user_id === me.id`

## Docs

- [x] `docs/guides/routes/dashboard/notifications.md` (staff alerts)
- [x] `docs/architecture/data-model.md`, `api-conventions.md`
- [x] `.cursor/rules/in-app-notifications.mdc`

## Exit criteria

- [x] `pnpm run ci:quality` green
- [x] pytest isolation/dedupe/mark-read
- [x] Cross-clinic list isolation test
