---
name: in-app-notifications
description: >-
  Staff Notification Center — create_notification, emit catalog, Redis WS,
  bell UI. Use when adding alerts, wiring service emit points, or changing
  notification types.
---

# In-app staff notifications

Always-on rule: `.cursor/rules/in-app-notifications.mdc`

## Add a new type

1. Extend CHECK constraint in a **new** Alembic migration (never edit `035`).
2. Add emit helper or call `create_notification` with audience + dedupe key.
3. Add icon in `apps/web/src/features/notifications/lib/notificationsDisplay.ts`.
4. Update route guide event list if user-visible behavior changes.

## Emit from services only

After primary `commit`, call the matching `notify_*` helper. Do not duplicate from `assistant/service.py`.

## Tests

`apps/api/tests/test_notifications.py` — dedupe, clinic isolation, mark-read.
