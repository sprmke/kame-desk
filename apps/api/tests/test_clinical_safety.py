import pytest
from httpx import AsyncClient

from tests.test_patients_appointments import _setup_clinic


@pytest.mark.asyncio
async def test_unknown_drug_is_unchecked(client: AsyncClient):
    ctx = await _setup_clinic(client)
    patient = await client.post(
        "/api/v1/patients",
        headers=ctx["headers"],
        json={"full_name": "Safety Patient", "data_processing_consent": True},
    )
    patient_id = patient.json()["id"]
    res = await client.post(
        f"/api/v1/patients/{patient_id}/prescription-conflicts",
        headers=ctx["headers"],
        json={"drug_names": ["NotARealDrugXYZ"]},
    )
    assert res.status_code == 200
    flags = res.json()["flags"]
    assert any(f["type"] == "unchecked" and f["drug_name"] == "NotARealDrugXYZ" for f in flags)


@pytest.mark.asyncio
async def test_order_lifecycle(client: AsyncClient):
    ctx = await _setup_clinic(client)
    patient = await client.post(
        "/api/v1/patients",
        headers=ctx["headers"],
        json={"full_name": "Order Patient", "data_processing_consent": True},
    )
    patient_id = patient.json()["id"]
    created = await client.post(
        f"/api/v1/patients/{patient_id}/orders",
        headers=ctx["headers"],
        json={"order_type": "lab", "name": "CBC"},
    )
    assert created.status_code == 200
    order_id = created.json()["id"]
    assert created.json()["status"] == "ordered"

    patched = await client.patch(
        f"/api/v1/patients/{patient_id}/orders/{order_id}",
        headers=ctx["headers"],
        json={"status": "resulted", "result_summary": "Within range"},
    )
    assert patched.status_code == 200
    assert patched.json()["status"] == "resulted"
    assert patched.json()["result_summary"] == "Within range"

    listed = await client.get(
        f"/api/v1/patients/{patient_id}/orders",
        headers=ctx["headers"],
    )
    assert listed.status_code == 200
    assert listed.json()[0]["id"] == order_id


@pytest.mark.asyncio
async def test_referral_fields(client: AsyncClient):
    ctx = await _setup_clinic(client)
    clinic_id = ctx["clinic_id"]
    template = await client.post(
        f"/api/v1/clinics/{clinic_id}/document-templates",
        headers=ctx["headers"],
        json={
            "template_key": "ref_safety",
            "name": "Referral",
            "template_type": "referral_letter",
            "body_template": "Refer {{patient.full_name}}",
        },
    )
    assert template.status_code == 200
    patient = await client.post(
        "/api/v1/patients",
        headers=ctx["headers"],
        json={"full_name": "Referral Patient", "data_processing_consent": True},
    )
    patient_id = patient.json()["id"]
    draft = await client.post(
        f"/api/v1/patients/{patient_id}/documents",
        headers=ctx["headers"],
        json={
            "template_id": template.json()["id"],
            "referral_recipient": "Dr. Cruz",
        },
    )
    assert draft.status_code == 200
    assert draft.json()["referral_recipient"] == "Dr. Cruz"
    assert draft.json()["referral_status"] == "draft"

    patched = await client.patch(
        f"/api/v1/documents/{draft.json()['id']}",
        headers=ctx["headers"],
        json={"referral_status": "sent", "referral_outcome": "Seen"},
    )
    assert patched.status_code == 200
    assert patched.json()["referral_status"] == "sent"
    assert patched.json()["referral_outcome"] == "Seen"


@pytest.mark.asyncio
async def test_specialty_templates_include_named_specialties(client: AsyncClient):
    ctx = await _setup_clinic(client)
    res = await client.get("/api/v1/specialty-templates", headers=ctx["headers"])
    assert res.status_code == 200
    keys = {t["template_key"] for t in res.json()}
    assert {
        "general",
        "dental",
        "pediatric",
        "obgyn",
        "psychiatry",
        "dermatology",
    }.issubset(keys)
