import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.core.db import AsyncSessionLocal
from app.models import ClinicMembership, Notification
from app.services.notification_service import create_notification, mark_read
from tests.conftest import register_owner


def _headers(ctx: dict) -> dict:
    token = ctx.get("tokens", {}).get("access_token") or ctx.get("access_token")
    return {
        "Authorization": f"Bearer {token}",
        "X-Clinic-Id": ctx["clinic_id"],
    }


@pytest.mark.asyncio
async def test_create_notification_dedupe(client: AsyncClient):
    ctx = await register_owner(client, suffix=f"nd-{uuid.uuid4().hex[:8]}")
    async with AsyncSessionLocal() as db:
        clinic_id = uuid.UUID(ctx["clinic_id"])
        row1 = await create_notification(
            db,
            clinic_id=clinic_id,
            type="waitlist.created",
            title="Waitlist entry",
            body="Jane Doe",
            dedupe_key="abc:created",
            audience_roles=["owner"],
        )
        await db.commit()
        assert row1 is not None
        row2 = await create_notification(
            db,
            clinic_id=clinic_id,
            type="waitlist.created",
            title="Waitlist entry",
            body="Jane Doe",
            dedupe_key="abc:created",
            audience_roles=["owner"],
        )
        await db.commit()
        assert row2 is None


@pytest.mark.asyncio
async def test_list_notifications_scoped_to_clinic(client: AsyncClient):
    ctx_a = await register_owner(client, suffix=f"na-{uuid.uuid4().hex[:8]}")
    ctx_b = await register_owner(client, suffix=f"nb-{uuid.uuid4().hex[:8]}")
    async with AsyncSessionLocal() as db:
        await create_notification(
            db,
            clinic_id=uuid.UUID(ctx_a["clinic_id"]),
            type="visit.arrived",
            title="Patient arrived",
            body="Test Patient",
            audience_roles=["owner"],
        )
        await db.commit()

    res = await client.get("/api/v1/notifications", headers=_headers(ctx_b))
    assert res.status_code == 200
    assert res.json()["total"] == 0

    res_a = await client.get("/api/v1/notifications", headers=_headers(ctx_a))
    assert res_a.status_code == 200
    assert res_a.json()["total"] >= 1


@pytest.mark.asyncio
async def test_mark_read_persists(client: AsyncClient):
    ctx = await register_owner(client, suffix=f"nr-{uuid.uuid4().hex[:8]}")
    async with AsyncSessionLocal() as db:
        clinic_id = uuid.UUID(ctx["clinic_id"])
        row = await create_notification(
            db,
            clinic_id=clinic_id,
            type="document.issued",
            title="Document issued",
            body="Patient",
            audience_roles=["owner"],
        )
        await db.commit()
        assert row is not None
        notif_id = row.id
        membership = await db.execute(
            select(ClinicMembership).where(
                ClinicMembership.clinic_id == clinic_id,
                ClinicMembership.user_id == uuid.UUID(ctx["user_id"]),
            )
        )
        mem = membership.scalar_one()
        await mark_read(db, mem, notif_id)

    res = await client.get("/api/v1/notifications", headers=_headers(ctx))
    items = res.json()["items"]
    match = next(i for i in items if i["id"] == str(notif_id))
    assert match["is_read"] is True


@pytest.mark.asyncio
async def test_notification_body_has_no_phi_fields(client: AsyncClient):
    ctx = await register_owner(client, suffix=f"np-{uuid.uuid4().hex[:8]}")
    async with AsyncSessionLocal() as db:
        row = await create_notification(
            db,
            clinic_id=uuid.UUID(ctx["clinic_id"]),
            type="prescription.issued",
            title="Prescription issued",
            body="Maria Santos",
            audience_roles=["owner"],
            metadata={"note": "no rx details"},
        )
        await db.commit()
        assert row is not None
        stored = await db.get(Notification, row.id)
        assert stored is not None
        assert "mg" not in (stored.body or "").lower()
        assert stored.metadata_.get("note") == "no rx details"
