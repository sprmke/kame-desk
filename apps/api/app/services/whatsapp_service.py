import logging
import os
import uuid
from typing import Any

import httpx

from app.services.sms_service import normalize_ph_e164

logger = logging.getLogger(__name__)

GRAPH_API_BASE = "https://graph.facebook.com/v20.0"

# MVP ships a small fixed set of pre-approved WhatsApp message templates
# (Meta requires business-initiated messages to use approved templates,
# not freeform text). Each takes one body text variable.
WHATSAPP_TEMPLATES: dict[str, str] = {
    "confirmation": "doctordesk_appointment_confirmation",
    "reminder_24h": "doctordesk_appointment_reminder",
    "reminder_2h": "doctordesk_appointment_reminder",
    "reschedule_notice": "doctordesk_appointment_rescheduled",
    "cancellation_notice": "doctordesk_appointment_cancelled",
}


async def send_whatsapp_template(
    *,
    to: str,
    reminder_type: str,
    body_param: str,
    reply_token: str,
    creds: dict[str, Any],
) -> str:
    """Send one WhatsApp template message. Returns provider message id.

    Never logs body or full number. The reply_token is attached as the
    payload of a Confirm/Cancel quick-reply button on the template so an
    inbound button tap can be matched back to this reminder without any
    free-text keyword parsing.
    """
    phone_number_id = str(creds.get("phone_number_id") or "").strip()
    access_token = str(creds.get("access_token") or "").strip()
    if not phone_number_id or not access_token:
        raise ValueError("WhatsApp Business credentials incomplete")

    destination = normalize_ph_e164(to).lstrip("+")
    template_name = WHATSAPP_TEMPLATES.get(reminder_type, WHATSAPP_TEMPLATES["reminder_24h"])

    if os.environ.get("DOCTORDESK_TESTING") == "1":
        return f"wamid.test_{uuid.uuid4().hex[:12]}"

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(
            f"{GRAPH_API_BASE}/{phone_number_id}/messages",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "messaging_product": "whatsapp",
                "to": destination,
                "type": "template",
                "template": {
                    "name": template_name,
                    "language": {"code": "en"},
                    "components": [
                        {
                            "type": "body",
                            "parameters": [{"type": "text", "text": body_param}],
                        },
                        {
                            "type": "button",
                            "sub_type": "quick_reply",
                            "index": "0",
                            "parameters": [{"type": "payload", "payload": reply_token}],
                        },
                    ],
                },
            },
        )
    if response.status_code >= 400:
        logger.warning(
            "WhatsApp send failed status=%s phone_number_id=%s",
            response.status_code,
            phone_number_id,
        )
        raise RuntimeError("WhatsApp send failed")
    payload = response.json()
    try:
        return str(payload["messages"][0]["id"])
    except (KeyError, IndexError) as exc:
        raise RuntimeError("WhatsApp response missing message id") from exc


def parse_whatsapp_inbound(payload: dict[str, Any]) -> dict[str, Any] | None:
    """Extract {phone_number_id, from, reply_token | None, text} from a Meta
    WhatsApp webhook payload, or None if the payload isn't a user message
    (e.g. a delivery-status callback). A quick-reply button tap carries the
    reply_token we attached when sending; freeform text has no reply_token
    and is not auto-matched to a reminder in MVP.
    """
    try:
        entry = payload["entry"][0]
        change = entry["changes"][0]
        value = change["value"]
        phone_number_id = value["metadata"]["phone_number_id"]
        messages = value.get("messages")
        if not messages:
            return None
        message = messages[0]
        from_number = message["from"]
        if message.get("type") == "button":
            return {
                "phone_number_id": phone_number_id,
                "from": from_number,
                "reply_token": message["button"]["payload"],
                "text": message["button"].get("text"),
            }
        if message.get("type") == "text":
            return {
                "phone_number_id": phone_number_id,
                "from": from_number,
                "reply_token": None,
                "text": message["text"]["body"],
            }
        return None
    except (KeyError, IndexError, TypeError):
        return None
