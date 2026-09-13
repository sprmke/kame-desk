import pytest
from httpx import AsyncClient

from tests.test_patients_appointments import _setup_clinic


def _csv(*rows: str) -> str:
    return "full_name,contact_number,birthdate,email\n" + "\n".join(rows)


@pytest.mark.asyncio
async def test_possible_matches_by_name_and_contact(client: AsyncClient):
    ctx = await _setup_clinic(client)
    created = await client.post(
        "/api/v1/patients",
        headers=ctx["headers"],
        json={
            "full_name": "Ana Reyes",
            "contact_number": "09170001111",
            "data_processing_consent": True,
        },
    )
    assert created.status_code == 200
    by_name = await client.get(
        "/api/v1/patients/matches",
        headers=ctx["headers"],
        params={"full_name": "Ana Reyes"},
    )
    assert by_name.status_code == 200
    assert any(p["id"] == created.json()["id"] for p in by_name.json())
    by_contact = await client.get(
        "/api/v1/patients/matches",
        headers=ctx["headers"],
        params={"contact_number": "09170001111"},
    )
    assert any(p["id"] == created.json()["id"] for p in by_contact.json())


@pytest.mark.asyncio
async def test_merge_reassigns_appointments_and_archives_source(client: AsyncClient):
    ctx = await _setup_clinic(client)
    target = await client.post(
        "/api/v1/patients",
        headers=ctx["headers"],
        json={"full_name": "Keep Chart", "data_processing_consent": True},
    )
    source = await client.post(
        "/api/v1/patients",
        headers=ctx["headers"],
        json={"full_name": "Dup Chart", "data_processing_consent": True},
    )
    assert target.status_code == 200
    assert source.status_code == 200
    target_id = target.json()["id"]
    source_id = source.json()["id"]
    appt = await client.post(
        "/api/v1/appointments",
        headers=ctx["headers"],
        json={
            "patient_id": source_id,
            "doctor_id": ctx["doctor_id"],
            "scheduled_start": "2026-11-02T10:00:00+08:00",
            "scheduled_end": "2026-11-02T10:30:00+08:00",
        },
    )
    assert appt.status_code == 200
    merged = await client.post(
        f"/api/v1/patients/{target_id}/merge",
        headers=ctx["headers"],
        json={"source_patient_id": source_id},
    )
    assert merged.status_code == 200
    listed = await client.get(
        "/api/v1/appointments",
        headers=ctx["headers"],
        params={"patient_id": target_id},
    )
    assert listed.status_code == 200
    assert any(row["id"] == appt.json()["id"] for row in listed.json()["items"])
    source_get = await client.get(f"/api/v1/patients/{source_id}", headers=ctx["headers"])
    assert source_get.status_code == 200
    assert source_get.json()["is_archived"] is True
    listed_patients = await client.get("/api/v1/patients", headers=ctx["headers"])
    ids = [p["id"] for p in listed_patients.json()["items"]]
    assert source_id not in ids


@pytest.mark.asyncio
async def test_import_dry_run_then_commit(client: AsyncClient):
    ctx = await _setup_clinic(client)
    csv_body = _csv(
        "Imported One,09170002222,1990-01-15,one@example.com",
        "Imported Two,,,",
    )
    preview = await client.post(
        "/api/v1/patients/import",
        headers=ctx["headers"],
        json={"csv": csv_body, "commit": False},
    )
    assert preview.status_code == 200
    assert preview.json()["committed"] is False
    assert preview.json()["created"] == 0
    assert len(preview.json()["items"]) == 2
    before = await client.get("/api/v1/patients", headers=ctx["headers"])
    before_count = before.json()["total"]
    committed = await client.post(
        "/api/v1/patients/import",
        headers=ctx["headers"],
        json={"csv": csv_body, "commit": True},
    )
    assert committed.status_code == 200
    assert committed.json()["committed"] is True
    assert committed.json()["created"] == 2
    after = await client.get("/api/v1/patients", headers=ctx["headers"])
    assert after.json()["total"] == before_count + 2


@pytest.mark.asyncio
async def test_import_requires_full_name_column(client: AsyncClient):
    ctx = await _setup_clinic(client)
    res = await client.post(
        "/api/v1/patients/import",
        headers=ctx["headers"],
        json={"csv": "name\nSomeone", "commit": False},
    )
    assert res.status_code == 400


@pytest.mark.asyncio
async def test_merge_rejects_self(client: AsyncClient):
    ctx = await _setup_clinic(client)
    patient = await client.post(
        "/api/v1/patients",
        headers=ctx["headers"],
        json={"full_name": "Solo", "data_processing_consent": True},
    )
    patient_id = patient.json()["id"]
    res = await client.post(
        f"/api/v1/patients/{patient_id}/merge",
        headers=ctx["headers"],
        json={"source_patient_id": patient_id},
    )
    assert res.status_code == 400
