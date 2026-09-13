import logging
import os
import re
import uuid
from typing import Any

import httpx

logger = logging.getLogger(__name__)

TWILIO_MESSAGES_URL = "https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json"


def normalize_ph_e164(raw: str) -> str:
    trimmed = raw.strip()
    digits = re.sub(r"\D", "", trimmed)
    if trimmed.startswith("+") and digits:
        return f"+{digits}"
    if digits.startswith("63") and len(digits) >= 12:
        return f"+{digits}"
    if digits.startswith("0") and len(digits) == 11:
        return f"+63{digits[1:]}"
    if digits.startswith("9") and len(digits) == 10:
        return f"+63{digits}"
    if digits:
        return f"+{digits}"
    raise ValueError("Phone number is empty")


async def send_twilio_sms(*, to: str, body: str, creds: dict[str, Any]) -> str:
    """Send one SMS. Returns provider message SID. Never logs body or full number."""
    account_sid = str(creds.get("account_sid") or "").strip()
    auth_token = str(creds.get("auth_token") or "").strip()
    from_number = str(creds.get("from_number") or "").strip()
    if not account_sid or not auth_token or not from_number:
        raise ValueError("Twilio credentials incomplete")

    destination = normalize_ph_e164(to)
    if os.environ.get("DOCTORDESK_TESTING") == "1":
        return f"SM_test_{uuid.uuid4().hex[:12]}"

    url = TWILIO_MESSAGES_URL.format(sid=account_sid)
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(
            url,
            auth=(account_sid, auth_token),
            data={"From": from_number, "To": destination, "Body": body},
        )
    if response.status_code >= 400:
        logger.warning(
            "Twilio SMS failed status=%s account=%s",
            response.status_code,
            account_sid[:6],
        )
        raise RuntimeError("Twilio SMS send failed")
    payload = response.json()
    sid = payload.get("sid")
    if not sid:
        raise RuntimeError("Twilio response missing sid")
    return str(sid)
