import json

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select

from app.core.config import settings
from app.models import SoapNote
from tests.test_patients_appointments import _setup_clinic
from tests.test_soap import _create_appointment


async def _read_sse_events(response) -> list[dict]:
    events: list[dict] = []
    async for line in response.aiter_lines():
        if not line.startswith("data: "):
            continue
        events.append(json.loads(line[6:]))
    return events


@pytest.mark.asyncio
async def test_soap_draft_streams_structured_fields(client: AsyncClient):
    ctx = await _setup_clinic(client)
    appt_id = await _create_appointment(client, ctx)

    async with client.stream(
        "POST",
        f"/api/v1/appointments/{appt_id}/soap-draft",
        headers=ctx["headers"],
        json={"input_text": "BP high, refill maintenance meds, follow up 2 weeks"},
    ) as res:
        assert res.status_code == 200
        events = await _read_sse_events(res)

    field_events = [e for e in events if e.get("type") == "field"]
    assert field_events
    fields = {e["field"] for e in field_events}
    assert {"subjective", "objective", "assessment", "plan"}.issubset(fields)
    assert any(e.get("type") == "done" for e in events)

    history = await client.get(
        f"/api/v1/appointments/{appt_id}/soap-notes",
        headers=ctx["headers"],
    )
    assert history.status_code == 200
    assert history.json()["items"] == []


@pytest.mark.asyncio
async def test_soap_draft_usage_cap_blocks(client: AsyncClient, monkeypatch):
    monkeypatch.setattr(settings, "ai_daily_request_cap", 1)
    ctx = await _setup_clinic(client)
    appt_id = await _create_appointment(client, ctx)

    first = await client.post(
        f"/api/v1/appointments/{appt_id}/soap-draft",
        headers=ctx["headers"],
        json={"input_text": "First draft"},
    )
    assert first.status_code == 200

    blocked = await client.post(
        f"/api/v1/appointments/{appt_id}/soap-draft",
        headers=ctx["headers"],
        json={"input_text": "Second draft"},
    )
    assert blocked.status_code == 429
    assert "unavailable today" in blocked.json()["detail"].lower()


@pytest.mark.asyncio
async def test_soap_draft_does_not_persist_without_save(client: AsyncClient):
    ctx = await _setup_clinic(client)
    appt_id = await _create_appointment(client, ctx)

    await client.post(
        f"/api/v1/appointments/{appt_id}/soap-draft",
        headers=ctx["headers"],
        json={"input_text": "Draft only"},
    )

    from app.core.db import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(func.count()).select_from(SoapNote).where(SoapNote.appointment_id == appt_id)
        )
        assert result.scalar_one() == 0


@pytest.mark.asyncio
async def test_soap_draft_endpoint_has_no_save_path(client: AsyncClient):
    from app.ai import soap_draft_service

    source = soap_draft_service.stream_soap_draft_sse.__code__.co_names
    assert "create_soap_version" not in source
