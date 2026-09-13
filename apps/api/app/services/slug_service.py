import re
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Clinic


def slugify_name(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug[:56] or f"clinic-{uuid.uuid4().hex[:8]}"


async def ensure_unique_slug(
    db: AsyncSession, base: str, exclude_id: uuid.UUID | None = None
) -> str:
    slug = base
    n = 2
    while True:
        q = select(Clinic.id).where(Clinic.slug == slug)
        if exclude_id:
            q = q.where(Clinic.id != exclude_id)
        existing = await db.execute(q)
        if existing.scalar_one_or_none() is None:
            return slug
        slug = f"{base}-{n}"
        n += 1
