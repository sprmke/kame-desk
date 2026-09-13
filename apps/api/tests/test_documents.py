import re
import uuid

import pytest
from httpx import AsyncClient

from app.core.db import AsyncSessionLocal
from app.models import DoctorProfile
from app.services.template_renderer import render_template, validate_template_body
from tests.test_patients_appointments import _setup_clinic


async def _stamp_doctor_signature(doctor_id: str) -> None:
    async with AsyncSessionLocal() as db:
        profile = await db.get(DoctorProfile, uuid.UUID(doctor_id))
        assert profile is not None
        profile.signature_image_key = "clinics/test/signature.png"
        await db.commit()


TEMPLATE_BODY = (
    "This certifies that {{patient.full_name}} was examined on {{visit.date}} at {{clinic.name}}."
)


def test_render_template_fills_placeholders():
    body = "Patient: {{patient.full_name}} at {{clinic.name}}"
    out = render_template(
        body,
        {"patient": {"full_name": "Maria Santos"}, "clinic": {"name": "Test Clinic"}},
    )
    assert out == "Patient: Maria Santos at Test Clinic"


def test_render_template_fills_placeholders_inside_html():
    body = "<p>Patient: <strong>{{patient.full_name}}</strong></p>"
    out = render_template(
        body,
        {"patient": {"full_name": "Maria Santos"}},
    )
    assert out == "<p>Patient: <strong>Maria Santos</strong></p>"


def test_render_template_fills_legacy_undotted_keys():
    out = render_template(
        "Seen {{patient_name}} on {{visit_date}}",
        {"patient": {"full_name": "Maria Santos"}, "visit": {"date": "2026-09-11"}},
    )
    assert out == "Seen Maria Santos on 2026-09-11"


def test_missing_placeholder_becomes_empty():
    out = render_template("Hello {{patient.full_name}}", {"patient": {}})
    assert out == "Hello "


def test_rejects_jinja_injection():
    with pytest.raises(ValueError):
        validate_template_body("{% import os %}")


def test_rejects_dunder_in_template():
    with pytest.raises(ValueError):
        validate_template_body("{{patient.__class__}}")


@pytest.mark.asyncio
async def test_document_issue_and_snapshot_immutable(client: AsyncClient, monkeypatch):
    monkeypatch.setattr(
        "app.services.document_service.upload_object_bytes",
        lambda key, body, ct: key,
    )
    monkeypatch.setattr(
        "app.services.document_pdf.render_document_pdf",
        lambda *args, **kwargs: b"%PDF-1.4",
    )

    ctx = await _setup_clinic(client)
    clinic_id = ctx["clinic_id"]
    await _stamp_doctor_signature(ctx["doctor_id"])

    template = await client.post(
        f"/api/v1/clinics/{clinic_id}/document-templates",
        headers=ctx["headers"],
        json={
            "template_key": "med_cert_default",
            "name": "Medical Certificate",
            "template_type": "medical_certificate",
            "body_template": TEMPLATE_BODY,
        },
    )
    assert template.status_code == 200
    template_id = template.json()["id"]

    patient = await client.post(
        "/api/v1/patients",
        headers=ctx["headers"],
        json={"full_name": "Doc Patient"},
    )
    patient_id = patient.json()["id"]

    draft = await client.post(
        f"/api/v1/patients/{patient_id}/documents",
        headers=ctx["headers"],
        json={"template_id": template_id},
    )
    assert draft.status_code == 200
    doc_id = draft.json()["id"]
    assert "Doc Patient" in draft.json()["preview_content"]

    issued = await client.post(
        f"/api/v1/documents/{doc_id}/issue",
        headers=ctx["headers"],
    )
    assert issued.status_code == 200
    snapshot = issued.json()["final_content_snapshot"]
    assert snapshot is not None

    await client.patch(
        f"/api/v1/clinics/{clinic_id}/document-templates/{template_id}",
        headers=ctx["headers"],
        json={"body_template": "Changed {{patient.full_name}}"},
    )

    history = await client.get(
        f"/api/v1/patients/{patient_id}/documents",
        headers=ctx["headers"],
    )
    assert history.json()["items"][0]["final_content_snapshot"] == snapshot

    files = await client.get(
        f"/api/v1/patients/{patient_id}/files",
        headers=ctx["headers"],
    )
    assert any(f["file_type"] == "clinical_document" for f in files.json())


@pytest.mark.asyncio
async def test_reception_cannot_create_document(client: AsyncClient, monkeypatch):
    captured: dict[str, str] = {}

    def fake_send(_email: str, accept_url: str, _clinic: str) -> None:
        captured["url"] = accept_url

    monkeypatch.setattr("app.services.clinic_service.send_invitation_email", fake_send)

    ctx = await _setup_clinic(client)
    clinic_id = ctx["clinic_id"]

    template = await client.post(
        f"/api/v1/clinics/{clinic_id}/document-templates",
        headers=ctx["headers"],
        json={
            "template_key": "referral_default",
            "name": "Referral",
            "template_type": "referral_letter",
            "body_template": "Refer {{patient.full_name}}",
        },
    )
    template_id = template.json()["id"]

    patient = await client.post(
        "/api/v1/patients",
        headers=ctx["headers"],
        json={"full_name": "Reception Test"},
    )
    patient_id = patient.json()["id"]

    inv = await client.post(
        f"/api/v1/clinics/{clinic_id}/invitations",
        headers=ctx["headers"],
        json={"email": f"reception-{uuid.uuid4().hex[:8]}@example.com", "role": "reception"},
    )
    token = re.search(r"token=([^&]+)", captured["url"]).group(1)
    await client.post(
        f"/api/v1/invitations/{token}/accept",
        json={"full_name": "Front Desk", "password": "password123"},
    )
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": inv.json()["email"], "password": "password123"},
    )
    reception_headers = {
        "Authorization": f"Bearer {login.json()['tokens']['access_token']}",
        "X-Clinic-Id": clinic_id,
    }

    blocked = await client.post(
        f"/api/v1/patients/{patient_id}/documents",
        headers=reception_headers,
        json={"template_id": template_id},
    )
    assert blocked.status_code == 403


@pytest.mark.asyncio
async def test_document_issue_requires_prc_and_signature(client: AsyncClient, monkeypatch):
    monkeypatch.setattr(
        "app.services.document_service.upload_object_bytes",
        lambda key, body, ct: key,
    )
    monkeypatch.setattr(
        "app.services.document_pdf.render_document_pdf",
        lambda *args, **kwargs: b"%PDF-1.4",
    )
    ctx = await _setup_clinic(client)
    clinic_id = ctx["clinic_id"]
    template = await client.post(
        f"/api/v1/clinics/{clinic_id}/document-templates",
        headers=ctx["headers"],
        json={
            "template_key": "med_cert_gate",
            "name": "Medical Certificate",
            "template_type": "medical_certificate",
            "body_template": TEMPLATE_BODY,
        },
    )
    patient = await client.post(
        "/api/v1/patients",
        headers=ctx["headers"],
        json={"full_name": "Gate Patient"},
    )
    draft = await client.post(
        f"/api/v1/patients/{patient.json()['id']}/documents",
        headers=ctx["headers"],
        json={"template_id": template.json()["id"]},
    )
    missing_sig = await client.post(
        f"/api/v1/documents/{draft.json()['id']}/issue",
        headers=ctx["headers"],
    )
    assert missing_sig.status_code == 400
    assert "Signature" in missing_sig.json()["detail"]

    await _stamp_doctor_signature(ctx["doctor_id"])
    issued = await client.post(
        f"/api/v1/documents/{draft.json()['id']}/issue",
        headers=ctx["headers"],
    )
    assert issued.status_code == 200


def test_html_body_to_blocks_keeps_marks_and_lists():
    from app.services.document_pdf import html_body_to_blocks, render_document_pdf

    blocks = html_body_to_blocks("<p>Hello <strong>world</strong></p><ul><li>One</li></ul>")
    xml = " ".join(chunk for _, chunk in blocks)
    assert "<b>world</b>" in xml
    assert "• One" in xml
    pdf = render_document_pdf("Clinic", "Cert", "<p>Hello <em>there</em></p>", signed=True)
    assert pdf.startswith(b"%PDF")
