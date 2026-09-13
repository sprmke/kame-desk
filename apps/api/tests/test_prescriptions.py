import pytest
from httpx import AsyncClient

from tests.test_patients_appointments import _setup_clinic

RX_ITEM = {
    "drug_name": "Paracetamol",
    "dosage": "500mg",
    "form": "tablet",
    "frequency": "every 6 hours",
    "duration": "5 days",
    "quantity": "20",
}


@pytest.mark.asyncio
async def test_prescription_conflict_and_override(client: AsyncClient, monkeypatch):
    monkeypatch.setattr(
        "app.services.prescription_service.upload_object_bytes",
        lambda key, body, ct: key,
    )
    monkeypatch.setattr(
        "app.services.prescription_pdf.render_prescription_pdf",
        lambda **kwargs: b"%PDF-1.4",
    )

    ctx = await _setup_clinic(client)
    patient = await client.post(
        "/api/v1/patients",
        headers=ctx["headers"],
        json={"full_name": "Rx Patient"},
    )
    patient_id = patient.json()["id"]
    await client.put(
        f"/api/v1/patients/{patient_id}/medical-info",
        headers=ctx["headers"],
        json={
            "allergies_reviewed": True,
            "allergies": [{"substance": "Penicillin", "reaction": "Rash", "severity": "moderate"}],
            "current_medications": [],
            "chronic_conditions": [],
            "vaccination_history": [],
        },
    )

    conflict = await client.post(
        f"/api/v1/patients/{patient_id}/prescription-conflicts",
        headers=ctx["headers"],
        json={"drug_names": ["Amoxicillin"]},
    )
    assert conflict.status_code == 200
    assert len(conflict.json()["flags"]) >= 1

    draft = await client.post(
        f"/api/v1/patients/{patient_id}/prescriptions",
        headers=ctx["headers"],
        json={"items": [{"drug_name": "Amoxicillin", "dosage": "500mg"}]},
    )
    assert draft.status_code == 200
    rx_id = draft.json()["id"]

    blocked = await client.post(
        f"/api/v1/prescriptions/{rx_id}/issue",
        headers=ctx["headers"],
        json={},
    )
    assert blocked.status_code == 409

    issued = await client.post(
        f"/api/v1/prescriptions/{rx_id}/issue",
        headers=ctx["headers"],
        json={"override_reason": "Patient tolerated prior course"},
    )
    assert issued.status_code == 200
    assert issued.json()["status"] == "issued"
    assert issued.json()["override_reason"] == "Patient tolerated prior course"


@pytest.mark.asyncio
async def test_prescription_issue_requires_license(client: AsyncClient, monkeypatch):
    monkeypatch.setattr(
        "app.services.prescription_service.upload_object_bytes",
        lambda key, body, ct: key,
    )
    monkeypatch.setattr(
        "app.services.prescription_pdf.render_prescription_pdf",
        lambda **kwargs: b"%PDF-1.4",
    )

    ctx = await _setup_clinic(client)
    clinic_id = ctx["clinic_id"]
    doctors = await client.get(f"/api/v1/clinics/{clinic_id}/doctors", headers=ctx["headers"])
    doctor_id = doctors.json()[0]["id"]
    await client.patch(
        f"/api/v1/doctors/{doctor_id}",
        headers=ctx["headers"],
        json={"prc_license_number": None},
    )

    patient = await client.post(
        "/api/v1/patients",
        headers=ctx["headers"],
        json={"full_name": "License Patient"},
    )
    patient_id = patient.json()["id"]

    draft = await client.post(
        f"/api/v1/patients/{patient_id}/prescriptions",
        headers=ctx["headers"],
        json={"items": [RX_ITEM]},
    )
    rx_id = draft.json()["id"]

    issue = await client.post(
        f"/api/v1/prescriptions/{rx_id}/issue",
        headers=ctx["headers"],
        json={},
    )
    assert issue.status_code == 400
    assert "PRC license" in issue.json()["detail"]


@pytest.mark.asyncio
async def test_void_prescription_keeps_row(client: AsyncClient, monkeypatch):
    monkeypatch.setattr(
        "app.services.prescription_service.upload_object_bytes",
        lambda key, body, ct: key,
    )
    monkeypatch.setattr(
        "app.services.prescription_pdf.render_prescription_pdf",
        lambda **kwargs: b"%PDF-1.4",
    )
    monkeypatch.setattr(
        "app.routers.prescriptions.create_presigned_download",
        lambda key: f"https://example.test/{key}",
    )

    ctx = await _setup_clinic(client)
    patient = await client.post(
        "/api/v1/patients",
        headers=ctx["headers"],
        json={"full_name": "Void Patient"},
    )
    patient_id = patient.json()["id"]

    draft = await client.post(
        f"/api/v1/patients/{patient_id}/prescriptions",
        headers=ctx["headers"],
        json={"items": [RX_ITEM]},
    )
    rx_id = draft.json()["id"]
    await client.post(
        f"/api/v1/prescriptions/{rx_id}/issue",
        headers=ctx["headers"],
        json={},
    )

    voided = await client.post(
        f"/api/v1/prescriptions/{rx_id}/void",
        headers=ctx["headers"],
        json={"reason": "Wrong patient"},
    )
    assert voided.status_code == 200
    assert voided.json()["status"] == "voided"
    assert voided.json()["void_reason"] == "Wrong patient"

    history = await client.get(
        f"/api/v1/patients/{patient_id}/prescriptions",
        headers=ctx["headers"],
    )
    assert history.status_code == 200
    assert len(history.json()["items"]) == 1


@pytest.mark.asyncio
async def test_prescription_history(client: AsyncClient):
    ctx = await _setup_clinic(client)
    patient = await client.post(
        "/api/v1/patients",
        headers=ctx["headers"],
        json={"full_name": "History Patient"},
    )
    patient_id = patient.json()["id"]

    draft = await client.post(
        f"/api/v1/patients/{patient_id}/prescriptions",
        headers=ctx["headers"],
        json={"items": [RX_ITEM]},
    )
    assert draft.status_code == 200

    history = await client.get(
        f"/api/v1/patients/{patient_id}/prescriptions",
        headers=ctx["headers"],
    )
    assert history.status_code == 200
    assert history.json()["total"] == 1
    assert history.json()["items"][0]["status"] == "draft"
