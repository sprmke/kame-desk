# Notifications (`/dashboard/settings/notifications`)

**Status:** Documented

## Behavior

- Owner/admin configure email, SMS, and WhatsApp reminders, lead-time toggles (confirmation, 24h, 2h), and sender name. Loading uses a form skeleton. Sender name and recall-condition fields use shared placeholders. Controls sit in divider rows (`SettingsSection` / `SettingsRow`).
- SMS requires Twilio credentials on first enable; API returns 400 if SMS is turned on without credentials. WhatsApp requires a Meta Business Cloud API phone number ID + access token on first enable, same 400-on-missing-credentials behavior.
- When credentials are saved, due SMS/WhatsApp reminders call the respective provider. A failed send is marked `failed` (never a fake success id).
- WhatsApp sends as a pre-approved message template (Meta requires this for business-initiated messages) with a Confirm/Cancel quick-reply button; tapping it resolves the reminder the same way the public reminder link does. See `docs/architecture/messaging-channels.md`.
- Chronic-condition recall rules are stored in `notification_preferences.chronic_condition_rules` (condition label + interval in months).

## Save paths

| Action | API                                            | DB                                                        |
| ------ | ---------------------------------------------- | --------------------------------------------------------- |
| Read   | `GET /clinics/{id}/notification-preferences`   | `clinics.notification_preferences`, Twilio/WhatsApp blobs |
| Update | `PATCH /clinics/{id}/notification-preferences` | merge prefs; encrypt Twilio/WhatsApp creds when provided  |

## RBAC

Owner and admin only.

## Implementation map

- Web: `apps/web/src/features/settings/notifications/pages/NotificationsSettingsPage.tsx`
- API: `apps/api/app/routers/recalls.py` (notification preference routes), `apps/api/app/routers/whatsapp_webhook.py` (inbound WhatsApp)
- Messaging adapters: `apps/api/app/services/messaging/`

## Host-facing knowledge

Turn on email reminders for confirmations and the 24h notice. SMS is optional and needs Twilio credentials in settings before it will send. WhatsApp is optional and needs a Meta WhatsApp Business phone number ID + access token before it will send. Add recall rules for chronic conditions (condition name and months between visits). If SMS or WhatsApp is enabled without credentials, saves are rejected so reminders are not silently dropped. After credentials are saved, sends actually go out through the provider; a failed send shows as failed, not sent.
