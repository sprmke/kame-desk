# Messaging channels (Phase 35)

**Status:** Documented

Reminders (confirmation, 24h, 2h, reschedule notice, cancellation notice) go out over one or more channels per clinic preference. Every channel implements the same adapter interface so `reminder_service.py` never branches on provider-specific wire formats — only on which channel is selected and whether that channel's clinic-level config/credentials are present.

## Interface

`app/services/messaging/base.py`:

```python
class OutboundMessage:
    to: str | None
    subject: str
    body: str
    reminder_type: str
    reply_token: str
    creds: dict[str, Any] | None = None
    sender_name: str | None = None

class MessageChannel(Protocol):
    name: str
    async def send(self, message: OutboundMessage) -> str: ...
    def parse_inbound_reply(self, payload: dict) -> dict | None: ...
```

`app/services/messaging/registry.py` exposes `get_channel(name) -> MessageChannel` backed by `CHANNELS = {"email", "sms", "whatsapp", "messenger", "viber"}`.

## Channels

| Channel     | Adapter                   | Provider                         | Status                     |
| ----------- | ------------------------- | -------------------------------- | -------------------------- |
| `email`     | `EmailChannel`            | SMTP (local) / Resend (prod)     | Shipped                    |
| `sms`       | `SmsChannel`              | Twilio                           | Shipped (Phase 26)         |
| `whatsapp`  | `WhatsAppChannel`         | Meta WhatsApp Business Cloud API | Shipped (Phase 35)         |
| `messenger` | `MessengerChannel` (stub) | —                                | Documented stub, not wired |
| `viber`     | `ViberChannel` (stub)     | —                                | Documented stub, not wired |

Messenger/Viber satisfy the `MessageChannel` protocol so a future phase can activate them without a data-model change, but `send`/`parse_inbound_reply` raise `NotImplementedError` — per the market-research plan's recommendation to validate WhatsApp with real pilot clinics before building all three (`clinic-software-market-research-feature-gaps.md` §5 open decision 5).

## Channel selection (`reminder_service.schedule_appointment_reminders`)

Additive, not fallback: a reminder row is created **per enabled channel** for each reminder type, not one row that tries channels in priority order. A patient with email + SMS + WhatsApp all enabled gets three separate reminder rows (and three sends) per reminder type.

A channel is added to a reminder's fan-out when:

- its clinic preference flag is on (`email_enabled` / `sms_enabled` / `whatsapp_enabled`), and
- the patient has the required contact info (`patient.email` for email; `patient.contact_number` for SMS/WhatsApp), and
- the clinic has valid provider config (`twilio_credentials_encrypted` for SMS; `whatsapp_credentials_encrypted` + `whatsapp_phone_number_id` for WhatsApp)

Missing config logs a warning and silently skips that channel — it never blocks the other channels or the appointment itself.

## WhatsApp specifics

- **Credentials:** `Clinic.whatsapp_phone_number_id` (plain, unique-indexed — used to route inbound webhook traffic to the right clinic) + `Clinic.whatsapp_credentials_encrypted` (Fernet-encrypted, holds `{"access_token": ...}`, same `secrets_crypto` pattern as Twilio). Set together via `PATCH /clinics/{id}/notification-preferences`.
- **Templates:** Meta requires business-initiated messages to use a pre-approved message template, not freeform text. MVP ships a small fixed set (`WHATSAPP_TEMPLATES` in `app/services/whatsapp_service.py`) mapping each reminder type to one template name, each taking one body-text variable plus a quick-reply Confirm/Cancel button.
- **Reply matching:** the reminder's `reply_token` is attached as the payload of the template's quick-reply button when sending. An inbound button tap carries that exact token back, so confirm/cancel resolution reuses the same `reminder_service.respond_to_reminder()` the public reminder-link endpoint uses — no keyword parsing of free text. Free-text WhatsApp replies (no button payload) are received but not auto-matched to a reminder in MVP.
- **Inbound webhook:** `GET/POST /api/v1/webhooks/whatsapp` (`app/routers/whatsapp_webhook.py`). `GET` handles Meta's subscription verification handshake (`hub.mode`/`hub.verify_token`/`hub.challenge` against `settings.whatsapp_webhook_verify_token`). `POST` receives all traffic for every clinic on one Meta App — it looks up the clinic by the payload's `phone_number_id`, and always returns 200 (even for unrecognized/ignored payloads) so Meta doesn't retry or disable the webhook.

## Testing pattern

Tests mock at the channel adapter module, not the underlying provider service or `reminder_service`'s old direct imports:

```python
monkeypatch.setattr("app.services.messaging.sms_channel.send_twilio_sms", fake_sms)
monkeypatch.setattr("app.services.messaging.email_channel.send_reminder_email", fake_send)
monkeypatch.setattr("app.services.messaging.whatsapp_channel.send_whatsapp_template", fake_whatsapp)
```

See `tests/test_reminders.py` (`test_sms_dispatch_sends_via_twilio`, `test_whatsapp_dispatch_sends_via_graph_api`), `tests/test_whatsapp_service.py` (payload parsing, template mapping), `tests/test_whatsapp_webhook.py` (verification handshake, button-reply confirm flow, unmatched/status-callback payloads are ignored).
