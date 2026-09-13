import json
import uuid

import pytest
from fastapi import HTTPException
from httpx import AsyncClient

from app.core.config import settings
from tests.test_patients_appointments import _setup_clinic


async def _clear_platform_ai_flag() -> None:
    from app.core.db import AsyncSessionLocal
    from app.models.platform import PlatformFeatureFlag

    async with AsyncSessionLocal() as db:
        flag = await db.get(PlatformFeatureFlag, "ai_assistant")
        if flag is not None:
            await db.delete(flag)
            await db.commit()


async def _enable_assistant(client: AsyncClient, ctx: dict, monkeypatch) -> None:
    await _clear_platform_ai_flag()
    monkeypatch.setattr(settings, "platform_ai_assistant_enabled", True)
    res = await client.patch(
        f"/api/v1/clinics/{ctx['clinic_id']}",
        headers=ctx["headers"],
        json={"ai_assistant_enabled": True},
    )
    assert res.status_code == 200


async def _create_conversation(client: AsyncClient, ctx: dict) -> str:
    res = await client.post("/api/v1/assistant/conversations", headers=ctx["headers"])
    assert res.status_code == 200
    return res.json()["id"]


async def _read_sse_events(response) -> list[dict]:
    events: list[dict] = []
    async for line in response.aiter_lines():
        if not line.startswith("data: "):
            continue
        events.append(json.loads(line[6:]))
    return events


async def _post_message_sse(
    client: AsyncClient,
    ctx: dict,
    conversation_id: str,
    content: str,
    *,
    page_context: dict | None = None,
) -> list[dict]:
    body = {"content": content}
    if page_context:
        body["page_context"] = page_context
    async with client.stream(
        "POST",
        f"/api/v1/assistant/conversations/{conversation_id}/messages",
        headers=ctx["headers"],
        json=body,
    ) as res:
        assert res.status_code == 200
        return await _read_sse_events(res)


@pytest.mark.asyncio
async def test_assistant_kill_switch_blocks(client: AsyncClient, monkeypatch):
    await _clear_platform_ai_flag()
    ctx = await _setup_clinic(client)
    monkeypatch.setattr(settings, "platform_ai_assistant_enabled", False)
    res = await client.post("/api/v1/assistant/conversations", headers=ctx["headers"])
    assert res.status_code == 503


@pytest.mark.asyncio
async def test_assistant_clinic_toggle_blocks(client: AsyncClient, monkeypatch):
    await _clear_platform_ai_flag()
    ctx = await _setup_clinic(client)
    monkeypatch.setattr(settings, "platform_ai_assistant_enabled", True)
    res = await client.post("/api/v1/assistant/conversations", headers=ctx["headers"])
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_tier0_search_patients(client: AsyncClient, monkeypatch):
    ctx = await _setup_clinic(client)
    await _enable_assistant(client, ctx, monkeypatch)
    await client.post(
        "/api/v1/patients",
        headers=ctx["headers"],
        json={"full_name": "Maria Santos"},
    )
    conv = await _create_conversation(client, ctx)
    events = await _post_message_sse(
        client,
        ctx,
        conv,
        '__tool__:{"name":"search_patients","args":{"q":"Maria"}}',
    )
    assert any(e.get("type") == "tool_result" for e in events)
    assert any(e.get("type") == "done" for e in events)


@pytest.mark.asyncio
async def test_tier2_cancel_requires_confirm(client: AsyncClient, monkeypatch):
    from datetime import UTC, datetime, timedelta

    ctx = await _setup_clinic(client)
    await _enable_assistant(client, ctx, monkeypatch)
    patient = await client.post(
        "/api/v1/patients",
        headers=ctx["headers"],
        json={"full_name": "Cancel Me"},
    )
    patient_id = patient.json()["id"]
    start = datetime(2026, 10, 15, 2, 0, tzinfo=UTC)
    end = start + timedelta(minutes=30)
    appt = await client.post(
        "/api/v1/appointments",
        headers=ctx["headers"],
        json={
            "patient_id": patient_id,
            "doctor_id": ctx["doctor_id"],
            "scheduled_start": start.isoformat(),
            "scheduled_end": end.isoformat(),
        },
    )
    appt_id = appt.json()["id"]
    conv = await _create_conversation(client, ctx)
    events = await _post_message_sse(
        client,
        ctx,
        conv,
        f'__tool__:{{"name":"propose_cancel_appointment","args":{{"appointment_id":"{appt_id}"}}}}',
    )
    confirm = next(e for e in events if e.get("type") == "confirm_card")
    action_id = confirm["action_id"]

    still = await client.get(f"/api/v1/appointments/{appt_id}", headers=ctx["headers"])
    assert still.json()["appointment_status"] == "Scheduled"

    cancel = await client.post(
        f"/api/v1/assistant/actions/{action_id}/cancel",
        headers=ctx["headers"],
    )
    assert cancel.status_code == 200

    confirm_res = await client.post(
        f"/api/v1/assistant/actions/{action_id}/confirm",
        headers=ctx["headers"],
    )
    assert confirm_res.status_code == 400


@pytest.mark.asyncio
async def test_tier2_confirm_cancel_writes(client: AsyncClient, monkeypatch):
    from datetime import UTC, datetime, timedelta

    ctx = await _setup_clinic(client)
    await _enable_assistant(client, ctx, monkeypatch)
    patient = await client.post(
        "/api/v1/patients",
        headers=ctx["headers"],
        json={"full_name": "Confirm Cancel"},
    )
    patient_id = patient.json()["id"]
    start = datetime(2026, 10, 16, 2, 0, tzinfo=UTC)
    end = start + timedelta(minutes=30)
    appt = await client.post(
        "/api/v1/appointments",
        headers=ctx["headers"],
        json={
            "patient_id": patient_id,
            "doctor_id": ctx["doctor_id"],
            "scheduled_start": start.isoformat(),
            "scheduled_end": end.isoformat(),
        },
    )
    appt_id = appt.json()["id"]
    conv = await _create_conversation(client, ctx)
    events = await _post_message_sse(
        client,
        ctx,
        conv,
        f'__tool__:{{"name":"propose_cancel_appointment","args":{{"appointment_id":"{appt_id}"}}}}',
    )
    action_id = next(e for e in events if e.get("type") == "confirm_card")["action_id"]
    confirmed = await client.post(
        f"/api/v1/assistant/actions/{action_id}/confirm",
        headers=ctx["headers"],
    )
    assert confirmed.status_code == 200
    updated = await client.get(f"/api/v1/appointments/{appt_id}", headers=ctx["headers"])
    assert updated.json()["appointment_status"] == "Cancelled"


@pytest.mark.asyncio
async def test_bulk_writes_escalate_to_tier2():
    from app.ai.assistant.context import PageContext, ResolvedContext
    from app.ai.assistant.tiers import PlannedToolCall, classify_tier

    ctx = ResolvedContext(page=PageContext())
    calls = [
        PlannedToolCall("propose_cancel_appointment", {}, 2, True),
        PlannedToolCall("propose_cancel_appointment", {}, 2, True),
    ]
    tier = classify_tier(calls[0], calls, ctx)
    assert tier == 2


@pytest.mark.asyncio
async def test_cross_scope_escalates():
    from app.ai.assistant.context import PageContext, ResolvedContext
    from app.ai.assistant.tiers import PlannedToolCall, classify_tier

    patient_a = uuid.uuid4()
    patient_b = uuid.uuid4()
    ctx = ResolvedContext(page=PageContext(patient_id=patient_a))
    call = PlannedToolCall(
        "propose_book_appointment",
        {"patient_id": str(patient_b)},
        1,
        True,
    )
    assert classify_tier(call, [call], ctx) == 2


@pytest.mark.asyncio
async def test_tier2_soap_requires_confirm(client: AsyncClient, monkeypatch):
    from datetime import UTC, datetime, timedelta

    ctx = await _setup_clinic(client)
    await _enable_assistant(client, ctx, monkeypatch)
    patient = await client.post(
        "/api/v1/patients",
        headers=ctx["headers"],
        json={"full_name": "SOAP Assist"},
    )
    patient_id = patient.json()["id"]
    start = datetime(2026, 10, 17, 2, 0, tzinfo=UTC)
    end = start + timedelta(minutes=30)
    appt = await client.post(
        "/api/v1/appointments",
        headers=ctx["headers"],
        json={
            "patient_id": patient_id,
            "doctor_id": ctx["doctor_id"],
            "scheduled_start": start.isoformat(),
            "scheduled_end": end.isoformat(),
        },
    )
    appt_id = appt.json()["id"]
    for status in ("Arrived", "In Consultation"):
        await client.post(
            f"/api/v1/appointments/{appt_id}/visit-status",
            headers=ctx["headers"],
            json={"visit_status": status},
        )

    conv = await _create_conversation(client, ctx)
    events = await _post_message_sse(
        client,
        ctx,
        conv,
        (
            '__tool__:{"name":"propose_save_soap_note","args":{'
            f'"appointment_id":"{appt_id}",'
            '"note":{"subjective":"Cough","objective":"Clear",'
            '"assessment":"URTI","plan":"Rest","specialty_template_key":"general"}'
            "}}"
        ),
    )
    confirm = next(e for e in events if e.get("type") == "confirm_card")
    action_id = confirm["action_id"]

    before = await client.get(
        f"/api/v1/appointments/{appt_id}/soap-notes",
        headers=ctx["headers"],
    )
    assert before.json()["latest_version"] is None

    confirmed = await client.post(
        f"/api/v1/assistant/actions/{action_id}/confirm",
        headers=ctx["headers"],
    )
    assert confirmed.status_code == 200

    after = await client.get(
        f"/api/v1/appointments/{appt_id}/soap-notes",
        headers=ctx["headers"],
    )
    assert after.json()["latest_version"] == 1


@pytest.mark.asyncio
async def test_never_build_tool_rejected():
    from app.ai.assistant.safety import assert_tool_registered

    with pytest.raises(HTTPException):
        assert_tool_registered("delete_patient")


@pytest.mark.asyncio
async def test_tier1_tool_error_emits_sse_error_no_write(client: AsyncClient, monkeypatch):
    from datetime import UTC, datetime, timedelta

    ctx = await _setup_clinic(client)
    await _enable_assistant(client, ctx, monkeypatch)
    patient = await client.post(
        "/api/v1/patients",
        headers=ctx["headers"],
        json={"full_name": "Book Fail"},
    )
    patient_id = patient.json()["id"]
    start = datetime(2026, 11, 1, 2, 0, tzinfo=UTC)
    end = start + timedelta(minutes=30)
    conv = await _create_conversation(client, ctx)
    bad_doctor = str(uuid.uuid4())
    events = await _post_message_sse(
        client,
        ctx,
        conv,
        (
            '__tool__:{"name":"propose_book_appointment","args":{'
            f'"patient_id":"{patient_id}",'
            f'"doctor_id":"{bad_doctor}",'
            f'"scheduled_start":"{start.isoformat()}",'
            f'"scheduled_end":"{end.isoformat()}"'
            "}}"
        ),
    )
    assert any(e.get("type") == "error" for e in events)
    assert not any(e.get("type") == "done" for e in events)
    listed = await client.get("/api/v1/appointments", headers=ctx["headers"])
    assert listed.json()["total"] == 0


@pytest.mark.asyncio
async def test_confirm_failure_leaves_state_unchanged(client: AsyncClient, monkeypatch):
    from datetime import UTC, datetime, timedelta

    ctx = await _setup_clinic(client)
    await _enable_assistant(client, ctx, monkeypatch)
    patient = await client.post(
        "/api/v1/patients",
        headers=ctx["headers"],
        json={"full_name": "Confirm Fail"},
    )
    patient_id = patient.json()["id"]
    start = datetime(2026, 11, 2, 2, 0, tzinfo=UTC)
    end = start + timedelta(minutes=30)
    appt = await client.post(
        "/api/v1/appointments",
        headers=ctx["headers"],
        json={
            "patient_id": patient_id,
            "doctor_id": ctx["doctor_id"],
            "scheduled_start": start.isoformat(),
            "scheduled_end": end.isoformat(),
        },
    )
    appt_id = appt.json()["id"]
    await client.patch(
        f"/api/v1/appointments/{appt_id}",
        headers=ctx["headers"],
        json={"appointment_status": "Cancelled"},
    )

    conv = await _create_conversation(client, ctx)
    events = await _post_message_sse(
        client,
        ctx,
        conv,
        f'__tool__:{{"name":"propose_cancel_appointment","args":{{"appointment_id":"{appt_id}"}}}}',
    )
    action_id = next(e for e in events if e.get("type") == "confirm_card")["action_id"]
    confirm_res = await client.post(
        f"/api/v1/assistant/actions/{action_id}/confirm",
        headers=ctx["headers"],
    )
    assert confirm_res.status_code == 409
    updated = await client.get(f"/api/v1/appointments/{appt_id}", headers=ctx["headers"])
    assert updated.json()["appointment_status"] == "Cancelled"


@pytest.mark.asyncio
async def test_natural_language_search_patients(client: AsyncClient, monkeypatch):
    from app.ai.assistant.orchestrator import ParsedToolCall
    from app.ai.assistant.planner import AssistantPlan

    async def fake_plan(content, page=None, attached=None):
        assert "Maria" in content
        return AssistantPlan(
            calls=[ParsedToolCall(name="search_patients", args={"q": "Maria"})],
            reply="",
        )

    monkeypatch.setattr("app.ai.assistant.service.plan_staff_turn", fake_plan)
    ctx = await _setup_clinic(client)
    await _enable_assistant(client, ctx, monkeypatch)
    await client.post(
        "/api/v1/patients",
        headers=ctx["headers"],
        json={"full_name": "Maria Santos"},
    )
    conv = await _create_conversation(client, ctx)
    events = await _post_message_sse(client, ctx, conv, "Find patient Maria Santos")
    results = [e for e in events if e.get("type") == "tool_result"]
    assert results
    names = [i.get("full_name") for i in results[0].get("result", {}).get("items", [])]
    assert "Maria Santos" in names


@pytest.mark.asyncio
async def test_booking_outside_hours_and_overlap_escalate():
    from app.ai.assistant.context import PageContext, ResolvedContext
    from app.ai.assistant.tiers import PlannedToolCall, classify_tier

    ctx = ResolvedContext(page=PageContext())
    late = PlannedToolCall(
        "propose_book_appointment",
        {"scheduled_start": "2026-10-14T20:00:00+08:00"},
        1,
        True,
    )
    assert classify_tier(late, [late], ctx) == 2
    overlap = PlannedToolCall(
        "propose_book_appointment",
        {"scheduled_start": "2026-10-14T10:00:00+08:00", "overlap_risk": True},
        1,
        True,
    )
    assert classify_tier(overlap, [overlap], ctx) == 2


@pytest.mark.asyncio
async def test_owner_can_read_ai_usage_and_disable_tool(client: AsyncClient, monkeypatch):
    ctx = await _setup_clinic(client)
    await _enable_assistant(client, ctx, monkeypatch)
    usage = await client.get("/api/v1/assistant/usage", headers=ctx["headers"])
    assert usage.status_code == 200
    assert "request_total" in usage.json()

    patched = await client.patch(
        f"/api/v1/clinics/{ctx['clinic_id']}",
        headers=ctx["headers"],
        json={"assistant_disabled_tools": ["propose_book_appointment"]},
    )
    assert patched.status_code == 200
    assert "propose_book_appointment" in patched.json()["assistant_disabled_tools"]

    from app.ai.assistant.planner import AssistantPlan, ParsedToolCall

    async def fake_plan(content, page=None, attached=None):
        return AssistantPlan(
            calls=[
                ParsedToolCall(
                    name="propose_book_appointment",
                    args={
                        "patient_id": str(uuid.uuid4()),
                        "doctor_id": ctx["doctor_id"],
                        "scheduled_start": "2026-10-14T02:00:00+00:00",
                        "scheduled_end": "2026-10-14T02:30:00+00:00",
                    },
                )
            ],
            reply="",
        )

    monkeypatch.setattr("app.ai.assistant.service.plan_staff_turn", fake_plan)
    conv = await _create_conversation(client, ctx)
    async with client.stream(
        "POST",
        f"/api/v1/assistant/conversations/{conv}/messages",
        headers=ctx["headers"],
        json={"content": "book a visit"},
    ) as res:
        events = await _read_sse_events(res)
    errors = [e for e in events if e.get("type") == "error"]
    assert errors
    assert "disabled" in str(errors[0].get("message", "")).lower()
