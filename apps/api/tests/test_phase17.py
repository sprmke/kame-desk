import base64

import pytest
from httpx import AsyncClient

from app.ai.billing_extract import extract_billing_fields_from_text, fixture_receipt_text
from app.ai.prescription_explain import explain_safety_flag_stub
from tests.test_billing import _create_patient
from tests.test_patients_appointments import _setup_clinic


@pytest.mark.asyncio
async def test_explain_flag_returns_text_without_changing_checker(client: AsyncClient):
    ctx = await _setup_clinic(client)
    patient_id = await _create_patient(client, ctx["headers"])
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
    flags = conflict.json()["flags"]
    assert flags

    flag = flags[0]
    res = await client.post(
        f"/api/v1/patients/{patient_id}/prescription-flag/explain",
        headers=ctx["headers"],
        json={"flag": flag},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["flag"] == flag
    assert len(body["explanation"]) > 10

    recheck = await client.post(
        f"/api/v1/patients/{patient_id}/prescription-conflicts",
        headers=ctx["headers"],
        json={"drug_names": ["Amoxicillin"]},
    )
    assert recheck.json()["flags"] == flags


@pytest.mark.asyncio
async def test_billing_extract_structured_draft(client: AsyncClient, monkeypatch):
    monkeypatch.setattr(
        "app.services.billing_assist_service.upload_object_bytes",
        lambda key, body, ct: key,
    )
    monkeypatch.setattr(
        "app.services.storage_service.create_presigned_download",
        lambda key: f"https://example.test/{key}",
    )

    ctx = await _setup_clinic(client)
    patient_id = await _create_patient(client, ctx["headers"])

    before = await client.get(
        f"/api/v1/patients/{patient_id}/invoices",
        headers=ctx["headers"],
    )
    assert before.status_code == 200
    assert before.json()["total"] == 0

    text = fixture_receipt_text()
    res = await client.post(
        f"/api/v1/patients/{patient_id}/billing-assist/extract",
        headers=ctx["headers"],
        json={
            "filename": "receipt.txt",
            "content_type": "text/plain",
            "content_base64": base64.b64encode(text.encode()).decode(),
        },
    )
    assert res.status_code == 200
    body = res.json()
    assert body["attempt_id"]
    assert body["fields"]["amount"]["value"] == "1250.00"
    assert body["fields"]["amount"]["confidence"] in ("high", "low")
    assert body["fields"]["date"]["value"] == "2026-09-01"
    assert body["fields"]["reference_number"]["value"] == "OR-2026-00421"

    after = await client.get(
        f"/api/v1/patients/{patient_id}/invoices",
        headers=ctx["headers"],
    )
    assert after.json()["total"] == 0

    confirm = await client.post(
        f"/api/v1/patients/{patient_id}/billing-assist/confirm-attempt",
        headers=ctx["headers"],
        json={"attempt_id": body["attempt_id"]},
    )
    assert confirm.status_code == 200


def test_billing_extract_heuristics_empty():
    fields = extract_billing_fields_from_text("")
    assert fields["amount"]["confidence"] == "missing"
    assert fields["amount"]["value"] is None


def test_explain_stub_mentions_drug():
    text = explain_safety_flag_stub(
        {
            "type": "allergy",
            "drug_name": "Amoxicillin",
            "related": "Penicillin",
            "message": "Allergy conflict",
        }
    )
    assert "Amoxicillin" in text
