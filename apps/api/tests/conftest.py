import os

# Set before any app.db import so tests get per-connection isolation (no pooled asyncpg across event loops).
os.environ.setdefault("DOCTORDESK_TESTING", "1")

import subprocess
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app

API_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session", autouse=True)
def migrated_db():
    alembic = API_ROOT / ".venv" / "bin" / "alembic"
    cmd = [str(alembic)] if alembic.exists() else ["uv", "run", "alembic"]
    result = subprocess.run(
        [*cmd, "upgrade", "head"],
        cwd=API_ROOT,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        pytest.skip(f"Database unavailable for API tests: {result.stderr}")


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


async def register_owner(client: AsyncClient, suffix: str = "1") -> dict:
    res = await client.post(
        "/api/v1/auth/register",
        json={
            "email": f"owner-{suffix}@example.com",
            "password": "password123",
            "full_name": "Dr Owner",
            "clinic_name": f"Test Clinic {suffix}",
        },
    )
    assert res.status_code == 200
    return res.json()
