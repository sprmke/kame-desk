import pytest

from app.services.whatsapp_service import (
    WHATSAPP_TEMPLATES,
    parse_whatsapp_inbound,
    send_whatsapp_template,
)


def _button_payload(payload: str = "reply-token-123", text: str = "Confirm") -> dict:
    return {
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "metadata": {"phone_number_id": "PHONE_ID_1"},
                            "messages": [
                                {
                                    "from": "639171234567",
                                    "type": "button",
                                    "button": {"payload": payload, "text": text},
                                }
                            ],
                        }
                    }
                ]
            }
        ]
    }


def _text_payload(body: str = "Hello") -> dict:
    return {
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "metadata": {"phone_number_id": "PHONE_ID_1"},
                            "messages": [
                                {
                                    "from": "639171234567",
                                    "type": "text",
                                    "text": {"body": body},
                                }
                            ],
                        }
                    }
                ]
            }
        ]
    }


def test_parse_inbound_button_reply_extracts_reply_token():
    parsed = parse_whatsapp_inbound(_button_payload())
    assert parsed == {
        "phone_number_id": "PHONE_ID_1",
        "from": "639171234567",
        "reply_token": "reply-token-123",
        "text": "Confirm",
    }


def test_parse_inbound_text_reply_has_no_reply_token():
    parsed = parse_whatsapp_inbound(_text_payload("please cancel"))
    assert parsed == {
        "phone_number_id": "PHONE_ID_1",
        "from": "639171234567",
        "reply_token": None,
        "text": "please cancel",
    }


def test_parse_inbound_ignores_status_callback():
    status_payload = {
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "metadata": {"phone_number_id": "PHONE_ID_1"},
                            "statuses": [{"id": "wamid.1", "status": "delivered"}],
                        }
                    }
                ]
            }
        ]
    }
    assert parse_whatsapp_inbound(status_payload) is None


def test_parse_inbound_malformed_payload_returns_none():
    assert parse_whatsapp_inbound({}) is None
    assert parse_whatsapp_inbound({"entry": []}) is None


def test_templates_exist_for_every_reminder_type():
    for reminder_type in (
        "confirmation",
        "reminder_24h",
        "reminder_2h",
        "reschedule_notice",
        "cancellation_notice",
    ):
        assert reminder_type in WHATSAPP_TEMPLATES


@pytest.mark.asyncio
async def test_send_whatsapp_template_requires_credentials():
    with pytest.raises(ValueError):
        await send_whatsapp_template(
            to="09171234567",
            reminder_type="reminder_24h",
            body_param="hello",
            reply_token="tok",
            creds={},
        )


@pytest.mark.asyncio
async def test_send_whatsapp_template_test_mode_short_circuit():
    message_id = await send_whatsapp_template(
        to="09171234567",
        reminder_type="reminder_24h",
        body_param="hello",
        reply_token="tok",
        creds={"phone_number_id": "PHONE_ID_1", "access_token": "token"},
    )
    assert message_id.startswith("wamid.test_")
