import pytest
from httpx import AsyncClient

from tests.test_patients_appointments import _setup_clinic


async def _create_patient(client: AsyncClient, headers: dict) -> str:
    resp = await client.post(
        "/api/v1/patients",
        headers=headers,
        json={"full_name": "Payer Test Patient", "data_processing_consent": True},
    )
    assert resp.status_code == 200
    return resp.json()["id"]


@pytest.mark.asyncio
async def test_payer_directory_crud(client: AsyncClient):
    ctx = await _setup_clinic(client)
    created = await client.post(
        "/api/v1/payers",
        headers=ctx["headers"],
        json={"name": "Maxicare", "payer_type": "hmo"},
    )
    assert created.status_code == 200
    payer_id = created.json()["id"]
    assert created.json()["is_active"] is True

    listed = await client.get("/api/v1/payers", headers=ctx["headers"])
    assert listed.status_code == 200
    assert any(p["id"] == payer_id for p in listed.json())

    updated = await client.patch(
        f"/api/v1/payers/{payer_id}",
        headers=ctx["headers"],
        json={"is_active": False},
    )
    assert updated.status_code == 200
    assert updated.json()["is_active"] is False


@pytest.mark.asyncio
async def test_eligibility_check_lifecycle(client: AsyncClient):
    ctx = await _setup_clinic(client)
    patient_id = await _create_patient(client, ctx["headers"])

    created = await client.post(
        "/api/v1/eligibility-checks",
        headers=ctx["headers"],
        json={
            "patient_id": patient_id,
            "payer_name": "PhilHealth",
            "payer_type": "philhealth",
            "member_id": "PH-1",
        },
    )
    assert created.status_code == 200
    assert created.json()["status"] == "pending"
    check_id = created.json()["id"]

    updated = await client.patch(
        f"/api/v1/eligibility-checks/{check_id}",
        headers=ctx["headers"],
        json={"status": "verified", "verified_amount": "2500.00"},
    )
    assert updated.status_code == 200
    assert updated.json()["status"] == "verified"
    assert updated.json()["verified_amount"] == "2500.00"

    listed = await client.get(
        "/api/v1/eligibility-checks",
        headers=ctx["headers"],
        params={"patient_id": patient_id},
    )
    assert listed.status_code == 200
    assert listed.json()["items"][0]["id"] == check_id
    assert listed.json()["items"][0]["patient_name"] == "Payer Test Patient"


@pytest.mark.asyncio
async def test_loa_request_lifecycle_and_claim_link(client: AsyncClient):
    ctx = await _setup_clinic(client)
    patient_id = await _create_patient(client, ctx["headers"])

    loa = await client.post(
        "/api/v1/loa-requests",
        headers=ctx["headers"],
        json={"patient_id": patient_id, "hmo_name": "Intellicare"},
    )
    assert loa.status_code == 200
    assert loa.json()["status"] == "requested"
    assert loa.json()["submitted_at"] is None
    loa_id = loa.json()["id"]

    submitted = await client.patch(
        f"/api/v1/loa-requests/{loa_id}",
        headers=ctx["headers"],
        json={"status": "submitted", "reference_number": "REF-1"},
    )
    assert submitted.status_code == 200
    assert submitted.json()["submitted_at"] is not None
    assert submitted.json()["decided_at"] is None

    approved = await client.patch(
        f"/api/v1/loa-requests/{loa_id}",
        headers=ctx["headers"],
        json={"status": "approved", "decision_notes": "Covered"},
    )
    assert approved.status_code == 200
    assert approved.json()["decided_at"] is not None

    claim = await client.post(
        "/api/v1/claims",
        headers=ctx["headers"],
        json={
            "patient_id": patient_id,
            "provider": "Intellicare",
            "payer_type": "hmo",
            "amount": "1000.00",
            "loa_request_id": loa_id,
        },
    )
    assert claim.status_code == 200
    assert claim.json()["payer_type"] == "hmo"
    assert claim.json()["loa_request_id"] == loa_id

    filtered = await client.get(
        "/api/v1/claims",
        headers=ctx["headers"],
        params={"payer_type": "hmo"},
    )
    assert filtered.status_code == 200
    assert any(c["id"] == claim.json()["id"] for c in filtered.json()["items"])


@pytest.mark.asyncio
async def test_loa_request_rejects_mismatched_claim(client: AsyncClient):
    ctx = await _setup_clinic(client)
    patient_a = await _create_patient(client, ctx["headers"])
    patient_b = await _create_patient(client, ctx["headers"])

    claim = await client.post(
        "/api/v1/claims",
        headers=ctx["headers"],
        json={"patient_id": patient_a, "provider": "Maxicare", "amount": "500.00"},
    )
    claim_id = claim.json()["id"]

    mismatched = await client.post(
        "/api/v1/loa-requests",
        headers=ctx["headers"],
        json={"patient_id": patient_b, "hmo_name": "Maxicare", "claim_id": claim_id},
    )
    assert mismatched.status_code == 400


@pytest.mark.asyncio
async def test_loa_request_can_link_claim_after_creation(client: AsyncClient):
    ctx = await _setup_clinic(client)
    patient_id = await _create_patient(client, ctx["headers"])

    loa = await client.post(
        "/api/v1/loa-requests",
        headers=ctx["headers"],
        json={"patient_id": patient_id, "hmo_name": "Maxicare"},
    )
    assert loa.status_code == 200
    assert loa.json()["claim_id"] is None
    loa_id = loa.json()["id"]

    claim = await client.post(
        "/api/v1/claims",
        headers=ctx["headers"],
        json={"patient_id": patient_id, "provider": "Maxicare", "amount": "750.00"},
    )
    claim_id = claim.json()["id"]

    linked = await client.patch(
        f"/api/v1/loa-requests/{loa_id}",
        headers=ctx["headers"],
        json={"claim_id": claim_id},
    )
    assert linked.status_code == 200
    assert linked.json()["claim_id"] == claim_id


@pytest.mark.asyncio
async def test_loa_request_link_rejects_mismatched_patient_claim(client: AsyncClient):
    ctx = await _setup_clinic(client)
    patient_a = await _create_patient(client, ctx["headers"])
    patient_b = await _create_patient(client, ctx["headers"])

    loa = await client.post(
        "/api/v1/loa-requests",
        headers=ctx["headers"],
        json={"patient_id": patient_a, "hmo_name": "Maxicare"},
    )
    loa_id = loa.json()["id"]

    claim = await client.post(
        "/api/v1/claims",
        headers=ctx["headers"],
        json={"patient_id": patient_b, "provider": "Maxicare", "amount": "750.00"},
    )
    claim_id = claim.json()["id"]

    mismatched = await client.patch(
        f"/api/v1/loa-requests/{loa_id}",
        headers=ctx["headers"],
        json={"claim_id": claim_id},
    )
    assert mismatched.status_code == 400


@pytest.mark.asyncio
async def test_eligibility_checks_search_filter_and_paginate(client: AsyncClient):
    ctx = await _setup_clinic(client)
    patient_id = await _create_patient(client, ctx["headers"])
    for payer, payer_type in (
        ("Maxicare", "hmo"),
        ("Intellicare", "hmo"),
        ("PhilHealth", "philhealth"),
    ):
        created = await client.post(
            "/api/v1/eligibility-checks",
            headers=ctx["headers"],
            json={
                "patient_id": patient_id,
                "payer_name": payer,
                "payer_type": payer_type,
            },
        )
        assert created.status_code == 200

    searched = await client.get(
        "/api/v1/eligibility-checks",
        headers=ctx["headers"],
        params={"q": "intelli"},
    )
    assert searched.status_code == 200
    assert [i["payer_name"] for i in searched.json()["items"]] == ["Intellicare"]

    by_type = await client.get(
        "/api/v1/eligibility-checks",
        headers=ctx["headers"],
        params={"payer_type": "hmo"},
    )
    assert by_type.json()["total"] == 2

    paged = await client.get(
        "/api/v1/eligibility-checks",
        headers=ctx["headers"],
        params={"page": 1, "page_size": 2, "sort": "payer:asc"},
    )
    assert paged.json()["total"] == 3
    assert [i["payer_name"] for i in paged.json()["items"]] == [
        "Intellicare",
        "Maxicare",
    ]

    second_page = await client.get(
        "/api/v1/eligibility-checks",
        headers=ctx["headers"],
        params={"page": 2, "page_size": 2, "sort": "payer:asc"},
    )
    assert [i["payer_name"] for i in second_page.json()["items"]] == ["PhilHealth"]


@pytest.mark.asyncio
async def test_loa_requests_search_and_paginate(client: AsyncClient):
    ctx = await _setup_clinic(client)
    patient_id = await _create_patient(client, ctx["headers"])
    for hmo in ("Maxicare", "Intellicare", "Medicard"):
        created = await client.post(
            "/api/v1/loa-requests",
            headers=ctx["headers"],
            json={"patient_id": patient_id, "hmo_name": hmo},
        )
        assert created.status_code == 200

    searched = await client.get(
        "/api/v1/loa-requests",
        headers=ctx["headers"],
        params={"q": "medicard"},
    )
    assert [i["hmo_name"] for i in searched.json()["items"]] == ["Medicard"]

    paged = await client.get(
        "/api/v1/loa-requests",
        headers=ctx["headers"],
        params={"page": 1, "page_size": 2, "sort": "payer:asc"},
    )
    assert paged.json()["total"] == 3
    assert [i["hmo_name"] for i in paged.json()["items"]] == [
        "Intellicare",
        "Maxicare",
    ]

    by_patient = await client.get(
        "/api/v1/loa-requests",
        headers=ctx["headers"],
        params={"patient_id": patient_id, "sort": "patient:asc"},
    )
    assert by_patient.json()["total"] == 3
