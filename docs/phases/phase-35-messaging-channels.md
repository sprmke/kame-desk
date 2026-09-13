# Phase 35: WhatsApp/Messenger/Viber messaging channel

**Status:** Done
**Depends on:** Phase 27
**Unlocks:** —

**Plan reference:** `docs/workflow/planned/clinic-software-market-research-feature-gaps.md` §4.1 #4

## Production defaults (resolves plan §5 open decision 5)

- Build the channel abstraction so any of WhatsApp/Messenger/Viber can plug in, but ship **WhatsApp Business Cloud API** first — it has the most mature official API of the three (Meta Graph API), the plan doc's PH competitor research cites it most often, and it covers both Messenger-adjacent and WhatsApp-native patient bases. Messenger/Viber stay as adapter stubs behind the same interface, not built speculatively, per the plan's own recommendation to validate with real pilot clinics before building all three.
- Pattern mirrors the existing Twilio SMS integration: per-clinic opt-in, per-clinic encrypted credentials, cost is clinic-metered where the channel has send cost.

## Goal

A clinic can enable WhatsApp as a reminder/confirmation channel alongside (not instead of) SMS/email, patients can reply on WhatsApp the same way they reply to SMS today (confirm/cancel/reschedule), and the channel is a first-class option next to `email`/`sms` everywhere reminders are configured.

## Tasks

### Backend

- [x] `app/services/messaging/` — channel adapter protocol (`send`, `parse_inbound_reply`) with `EmailChannel`, `SmsChannel` (existing Twilio logic moved behind the interface, no behavior change — verified by the pre-existing SMS/email tests continuing to pass against the new adapter modules), new `WhatsAppChannel` (WhatsApp Business Cloud API)
- [x] Extend `REMINDER_CHANNELS` to include `whatsapp`; `Reminder.channel` accepts it
- [x] Extend `Clinic`: `whatsapp_credentials_encrypted` (same encryption pattern as `twilio_credentials_encrypted`, holds `{access_token}`), `whatsapp_enabled`, plus `whatsapp_phone_number_id` (plain, unique-indexed — needed as the webhook routing key since one Meta App serves every clinic)
- [x] Inbound webhook router (`app/routers/whatsapp_webhook.py`) for WhatsApp reply parsing — button-tap replies carry the reminder's `reply_token` as the button payload (attached when the template is sent), routed through the same `respond_to_reminder()` service function the public reminder-link endpoint uses
- [x] `activity_log`: reuses existing `reminder.*`/`appointment.*` events, channel is already a field on `Reminder`

### Frontend

- [x] Settings → Notifications: WhatsApp Business credentials entry (phone number ID + access token) + enable toggle (mirrors existing Twilio settings UI)
- [x] Reminder channel selector: not applicable — channel is derived server-side from clinic prefs + patient data availability, same as SMS/email; the enable toggle in Settings → Notifications is the channel selector
- [x] Reminder dashboard shows WhatsApp delivery status alongside SMS/email (each row already displays raw `channel`/`status` strings, needed no schema change)

## Edge cases

- Clinic enables WhatsApp without valid Business API credentials → `PATCH /clinics/{id}/notification-preferences` returns 400, does not silently fail sends later (`test_whatsapp_blocked_without_credentials`)
- Patient has no WhatsApp-capable number on file (`patient.contact_number` unset) → that reminder row is never created for the `whatsapp` channel; other enabled channels (email/SMS) are unaffected — reminders fan out additively per channel, there is no single-channel "fallback" chain to fall back within (see `docs/architecture/messaging-channels.md` § Channel selection)
- WhatsApp template-message approval requirement (Meta requires pre-approved templates for business-initiated messages) → MVP ships a small fixed set of templates (`WHATSAPP_TEMPLATES` in `app/services/whatsapp_service.py`: confirmation, reminder, rescheduled, cancelled), not freeform text
- Two clinics configuring the same `whatsapp_phone_number_id` → rejected with 400 on save (DB also enforces a unique index as a second line of defense) — this is the webhook's only routing key across all clinics, so it must stay unique
- Malformed or unrecognized inbound webhook payload (delivery-status callback, unknown message type, unmatched `phone_number_id`) → webhook always returns 200 with `{"status": "ignored"}` rather than erroring, so Meta doesn't retry or disable the subscription

## Docs to update

- [x] `docs/mvp.md` §6.9 — add WhatsApp to delivery channels
- [x] `docs/tech-stack.md` — new external dependency (WhatsApp Business Cloud API)
- [x] `docs/architecture/messaging-channels.md` — new doc, the messaging adapter pattern
- [x] `docs/architecture/data-model.md` — new `Clinic` columns
- [x] `docs/guides/routes/dashboard/settings/notifications.md`, `docs/guides/routes/dashboard/reminders.md`, `docs/guides/routes/reminders.md`

## Exit criteria

- [x] WhatsApp reminders send and inbound button-tap replies resolve confirm/cancel through the same `respond_to_reminder()` path as the public reminder link. Reschedule-request has no WhatsApp button equivalent (template quick-reply buttons carry only a fixed payload, not free text) — patients requesting a reschedule via WhatsApp still use the reply-token link embedded in the template body, same as email/SMS.
- [x] Messenger/Viber adapters exist as documented stubs (interface satisfied, not wired to a live API) so a future phase can activate them without a data-model change
- [x] `pnpm run ci:quality` green
