from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient

from tests.test_patients_appointments import _setup_clinic


@pytest.mark.asyncio
async def test_patient_list_pagination_and_sort(client: AsyncClient):
    ctx = await _setup_clinic(client)
    for name in ("Zed Patient", "Amy Patient", "Mia Patient"):
        created = await client.post(
            "/api/v1/patients",
            headers=ctx["headers"],
            json={"full_name": name, "data_processing_consent": True},
        )
        assert created.status_code == 200

    page = await client.get(
        "/api/v1/patients",
        headers=ctx["headers"],
        params={"page": 1, "page_size": 2, "sort": "name:asc"},
    )
    assert page.status_code == 200
    body = page.json()
    assert body["page"] == 1
    assert body["page_size"] == 2
    assert body["total"] >= 3
    assert len(body["items"]) == 2
    names = [row["full_name"] for row in body["items"]]
    assert names == sorted(names)


@pytest.mark.asyncio
async def test_appointment_list_pagination(client: AsyncClient):
    ctx = await _setup_clinic(client)
    patients = []
    for name in ("One Patient", "Two Patient", "Three Patient"):
        created = await client.post(
            "/api/v1/patients",
            headers=ctx["headers"],
            json={"full_name": name, "data_processing_consent": True},
        )
        assert created.status_code == 200
        patients.append(created.json()["id"])

    start = datetime(2026, 10, 6, 2, 0, tzinfo=UTC)
    for index, patient_id in enumerate(patients):
        slot = start + timedelta(hours=index)
        booked = await client.post(
            "/api/v1/appointments",
            headers=ctx["headers"],
            json={
                "patient_id": patient_id,
                "doctor_id": ctx["doctor_id"],
                "scheduled_start": slot.isoformat(),
                "scheduled_end": (slot + timedelta(minutes=30)).isoformat(),
            },
        )
        assert booked.status_code == 200

    page = await client.get(
        "/api/v1/appointments",
        headers=ctx["headers"],
        params={"page": 1, "page_size": 2, "sort": "start:asc"},
    )
    assert page.status_code == 200
    body = page.json()
    assert body["total"] >= 3
    assert len(body["items"]) == 2
    assert body["page_size"] == 2

    unpaged = await client.get("/api/v1/appointments", headers=ctx["headers"])
    assert unpaged.status_code == 200
    assert unpaged.json()["total"] >= 3
    assert len(unpaged.json()["items"]) >= 3


@pytest.mark.asyncio
async def test_invoice_list_pagination(client: AsyncClient):
    ctx = await _setup_clinic(client)
    created = await client.post(
        "/api/v1/patients",
        headers=ctx["headers"],
        json={"full_name": "Bill Patient", "data_processing_consent": True},
    )
    assert created.status_code == 200
    patient_id = created.json()["id"]
    for amount in ("100.00", "200.00", "300.00"):
        invoice = await client.post(
            f"/api/v1/patients/{patient_id}/invoices",
            headers=ctx["headers"],
            json={
                "line_items": [{"description": "Consult", "quantity": "1", "unit_price": amount}]
            },
        )
        assert invoice.status_code == 200

    page = await client.get(
        "/api/v1/invoices",
        headers=ctx["headers"],
        params={"page": 1, "page_size": 2, "sort": "total:desc"},
    )
    assert page.status_code == 200
    body = page.json()
    assert body["page_size"] == 2
    assert body["total"] >= 3
    assert len(body["items"]) == 2
    totals = [float(row["total"]) for row in body["items"]]
    assert totals == sorted(totals, reverse=True)

    unpaged = await client.get("/api/v1/invoices", headers=ctx["headers"])
    assert unpaged.status_code == 200
    assert len(unpaged.json()["items"]) >= 3


@pytest.mark.asyncio
async def test_claim_list_pagination_and_search(client: AsyncClient):
    ctx = await _setup_clinic(client)
    created = await client.post(
        "/api/v1/patients",
        headers=ctx["headers"],
        json={"full_name": "Claim Patient", "data_processing_consent": True},
    )
    assert created.status_code == 200
    patient_id = created.json()["id"]
    for provider in ("Alpha HMO", "Beta Care", "Gamma Cover"):
        claim = await client.post(
            "/api/v1/claims",
            headers=ctx["headers"],
            json={
                "patient_id": patient_id,
                "provider": provider,
                "payer_type": "hmo",
                "amount": "500.00",
            },
        )
        assert claim.status_code == 200

    page = await client.get(
        "/api/v1/claims",
        headers=ctx["headers"],
        params={"page": 1, "page_size": 2, "q": "Beta", "sort": "created_at:desc"},
    )
    assert page.status_code == 200
    body = page.json()
    assert body["page_size"] == 2
    assert body["total"] == 1
    assert body["items"][0]["provider"] == "Beta Care"


@pytest.mark.asyncio
async def test_activity_log_search_and_sort(client: AsyncClient):
    ctx = await _setup_clinic(client)
    await client.post(
        "/api/v1/patients",
        headers=ctx["headers"],
        json={"full_name": "Log Patient", "data_processing_consent": True},
    )
    listed = await client.get(
        f"/api/v1/clinics/{ctx['clinic_id']}/activity-log",
        headers=ctx["headers"],
        params={"page": 1, "page_size": 2, "q": "patient.created", "sort": "created_at:desc"},
    )
    assert listed.status_code == 200
    body = listed.json()
    assert body["page_size"] == 2
    assert body["total"] >= 1
    assert all("patient.created" in row["action"] for row in body["items"])
