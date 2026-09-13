import json

import pytest
from httpx import AsyncClient

from app.ai.patient_assistant.context import sanitize_grounding_facts
from app.ai.patient_assistant.safety import verify_output_safety
from tests.test_patients_appointments import _setup_clinic


def test_grounding_facts_exclude_patient_fields():
    dirty = {
        "clinic_name": "Demo",
        "patient_name": "Maria",
        "nested": {"contact_number": "0917", "services": []},
    }
    clean = sanitize_grounding_facts(dirty)
    assert "patient_name" not in clean
    assert "contact_number" not in clean["nested"]


def test_output_safety_rejects_hmo_claim():
    grounding = {"accepts_hmo": False}
    out = verify_output_safety("Yes, we accept all major HMO plans.", grounding)
    assert "contact the clinic" in out.lower()


@pytest.mark.asyncio
async def test_patient_assistant_faq_sse(client: AsyncClient):
    ctx = await _setup_clinic(client)
    clinic = await client.get(
        f"/api/v1/clinics/{ctx['clinic_id']}",
        headers=ctx["headers"],
    )
    slug = clinic.json()["slug"]
    async with client.stream(
        "POST",
        f"/api/v1/public/clinics/{slug}/assistant/messages",
        json={"content": "What are your hours?"},
    ) as res:
        assert res.status_code == 200
        events = []
        async for line in res.aiter_lines():
            if line.startswith("data: "):
                events.append(json.loads(line[6:]))
    assert any(e.get("type") == "text" for e in events)


@pytest.mark.asyncio
async def test_patient_assistant_llm_plan_can_book(client: AsyncClient, monkeypatch):
    from datetime import date

    from app.ai.assistant.orchestrator import ParsedToolCall
    from app.ai.assistant.planner import AssistantPlan

    ctx = await _setup_clinic(client)
    clinic = await client.get(
        f"/api/v1/clinics/{ctx['clinic_id']}",
        headers=ctx["headers"],
    )
    slug = clinic.json()["slug"]
    on_date = date(2026, 11, 2)
    slots = await client.get(
        f"/api/v1/public/clinics/{slug}/available-slots"
        f"?doctor_id={ctx['doctor_id']}&date={on_date.isoformat()}"
    )
    assert slots.status_code == 200
    slot = slots.json()["slots"][0]

    async def fake_plan(content, grounding, *, allow_explicit_tools):
        return AssistantPlan(
            calls=[
                ParsedToolCall(
                    name="book_public_appointment",
                    args={
                        "doctor_id": ctx["doctor_id"],
                        "scheduled_start": slot["scheduled_start"],
                        "scheduled_end": slot["scheduled_end"],
                        "full_name": "Guest Booker",
                        "contact_number": "09170000002",
                    },
                )
            ]
        )

    monkeypatch.setattr("app.ai.patient_assistant.service.plan_patient_turn", fake_plan)
    events = []
    async with client.stream(
        "POST",
        f"/api/v1/public/clinics/{slug}/assistant/messages",
        json={"content": "Book me Tuesday morning"},
    ) as res:
        assert res.status_code == 200
        async for line in res.aiter_lines():
            if line.startswith("data: "):
                events.append(json.loads(line[6:]))
    assert any(e.get("type") == "tool_result" for e in events)
    assert any(
        "submitted" in (e.get("content") or "").lower() for e in events if e.get("type") == "text"
    )


@pytest.mark.asyncio
async def test_visit_summary_requires_approval(client: AsyncClient, monkeypatch):
    monkeypatch.setattr(
        "app.services.visit_summary_service.send_reminder_email",
        lambda *args, **kwargs: "smtp-local",
    )
    ctx = await _setup_clinic(client)
    patient = await client.post(
        "/api/v1/patients",
        headers=ctx["headers"],
        json={"full_name": "Summary Patient", "email": "patient@example.com"},
    )
    patient_id = patient.json()["id"]
    appt = await client.post(
        "/api/v1/appointments",
        headers=ctx["headers"],
        json={
            "patient_id": patient_id,
            "doctor_id": ctx["doctor_id"],
            "scheduled_start": "2026-10-15T10:00:00+08:00",
            "scheduled_end": "2026-10-15T10:30:00+08:00",
        },
    )
    appt_id = appt.json()["id"]
    for status in ("Arrived", "In Consultation", "Completed"):
        await client.post(
            f"/api/v1/appointments/{appt_id}/visit-status",
            headers=ctx["headers"],
            json={"visit_status": status},
        )

    draft = await client.get(
        f"/api/v1/appointments/{appt_id}/visit-summary",
        headers=ctx["headers"],
    )
    assert draft.status_code == 200
    assert draft.json()["status"] == "draft"

    sent = await client.post(
        f"/api/v1/appointments/{appt_id}/visit-summary/approve",
        headers=ctx["headers"],
        json={"edited_text": "Thanks for visiting."},
    )
    assert sent.status_code == 200
    assert sent.json()["status"] == "sent"

    rows = await client.get(
        f"/api/v1/appointments/{appt_id}/visit-summary",
        headers=ctx["headers"],
    )
    assert rows.json()["status"] == "sent"


@pytest.mark.asyncio
async def test_visit_summary_generation_failure_requires_manual_text(
    client: AsyncClient, monkeypatch
):
    monkeypatch.setattr(
        "app.services.visit_summary_service.send_reminder_email",
        lambda *args, **kwargs: "smtp-local",
    )

    async def fail_generate(_chart: str) -> tuple[str, bool]:
        return "", True

    monkeypatch.setattr(
        "app.services.visit_summary_service._generate_summary_text",
        fail_generate,
    )
    ctx = await _setup_clinic(client)
    patient = await client.post(
        "/api/v1/patients",
        headers=ctx["headers"],
        json={"full_name": "Failed Summary", "email": "patient@example.com"},
    )
    patient_id = patient.json()["id"]
    appt = await client.post(
        "/api/v1/appointments",
        headers=ctx["headers"],
        json={
            "patient_id": patient_id,
            "doctor_id": ctx["doctor_id"],
            "scheduled_start": "2026-10-16T10:00:00+08:00",
            "scheduled_end": "2026-10-16T10:30:00+08:00",
        },
    )
    appt_id = appt.json()["id"]
    for status in ("Arrived", "In Consultation", "Completed"):
        await client.post(
            f"/api/v1/appointments/{appt_id}/visit-status",
            headers=ctx["headers"],
            json={"visit_status": status},
        )

    draft = await client.get(
        f"/api/v1/appointments/{appt_id}/visit-summary",
        headers=ctx["headers"],
    )
    assert draft.status_code == 200
    body = draft.json()
    assert body["generation_failed"] is True
    assert body["generated_text"] == ""

    blocked = await client.post(
        f"/api/v1/appointments/{appt_id}/visit-summary/approve",
        headers=ctx["headers"],
        json={"edited_text": "  "},
    )
    assert blocked.status_code == 400

    sent = await client.post(
        f"/api/v1/appointments/{appt_id}/visit-summary/approve",
        headers=ctx["headers"],
        json={"edited_text": "Thanks for visiting. Follow the written plan."},
    )
    assert sent.status_code == 200
    assert sent.json()["status"] == "sent"
