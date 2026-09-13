import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Organization
from app.services.slug_service import slugify_name


async def ensure_unique_org_slug(
    db: AsyncSession, base: str, exclude_id: uuid.UUID | None = None
) -> str:
    slug = base
    n = 2
    while True:
        q = select(Organization.id).where(Organization.slug == slug)
        if exclude_id:
            q = q.where(Organization.id != exclude_id)
        existing = await db.execute(q)
        if existing.scalar_one_or_none() is None:
            return slug
        slug = f"{base}-{n}"
        n += 1


def org_slug_from_name(name: str) -> str:
    return slugify_name(name)[:56] or f"org-{uuid.uuid4().hex[:8]}"
