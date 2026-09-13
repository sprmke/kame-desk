import uuid
from datetime import UTC, date, datetime, time
from zoneinfo import ZoneInfo

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pagination import parse_sort
from app.models import ActivityLog, Clinic, ClinicMembership, User

MANILA = ZoneInfo("Asia/Manila")
CLINICAL_ACTION_PREFIXES = ("soap.",)
AUDIT_VIEW_ROLES = ("owner", "admin", "doctor")


def assert_audit_log_access(membership: ClinicMembership) -> None:
    if membership.role not in AUDIT_VIEW_ROLES:
        raise HTTPException(status_code=403, detail="Not allowed")


def _date_bounds(
    from_date: date | None, to_date: date | None
) -> tuple[datetime | None, datetime | None]:
    if from_date is None and to_date is None:
        return None, None
    start = None
    end = None
    if from_date:
        start = datetime.combine(from_date, time.min, tzinfo=MANILA).astimezone(UTC)
    if to_date:
        end = datetime.combine(to_date, time.max, tzinfo=MANILA).astimezone(UTC)
    return start, end


def _redact_row(
    row: ActivityLog,
    membership: ClinicMembership,
    actor_name: str | None,
) -> dict:
    metadata = row.metadata_
    summary = row.summary
    if membership.role == "admin" and any(
        row.action.startswith(p) for p in CLINICAL_ACTION_PREFIXES
    ):
        metadata = None
    return {
        "id": row.id,
        "clinic_id": row.clinic_id,
        "actor_user_id": row.actor_user_id,
        "actor_name": actor_name,
        "actor_type": row.actor_type,
        "action": row.action,
        "target_type": row.target_type,
        "target_id": row.target_id,
        "summary": summary,
        "metadata_": metadata,
        "created_at": row.created_at,
    }


async def list_clinic_activity_log(
    db: AsyncSession,
    clinic: Clinic,
    membership: ClinicMembership,
    *,
    page: int = 1,
    page_size: int = 50,
    actor_type: str | None = None,
    action: str | None = None,
    target_type: str | None = None,
    target_id: str | None = None,
    from_date: date | None = None,
    to_date: date | None = None,
    q: str | None = None,
    sort: str | None = None,
) -> tuple[list[dict], int]:
    assert_audit_log_access(membership)

    page_size = min(max(page_size, 1), 100)
    page = max(page, 1)

    filters = [ActivityLog.clinic_id == clinic.id]
    if actor_type:
        filters.append(ActivityLog.actor_type == actor_type)
    if action:
        filters.append(ActivityLog.action == action)
    if target_type:
        filters.append(ActivityLog.target_type == target_type)
    if target_id:
        filters.append(ActivityLog.target_id == target_id)
    if q and q.strip():
        term = f"%{q.strip()}%"
        filters.append(ActivityLog.action.ilike(term))
    start, end = _date_bounds(from_date, to_date)
    if start:
        filters.append(ActivityLog.created_at >= start)
    if end:
        filters.append(ActivityLog.created_at <= end)

    count_q = await db.execute(select(func.count()).select_from(ActivityLog).where(*filters))
    total = int(count_q.scalar_one())

    offset = (page - 1) * page_size
    rows = await db.execute(
        select(ActivityLog)
        .where(*filters)
        .order_by(parse_sort(sort, {"created_at": ActivityLog.created_at}, "created_at", "desc"))
        .offset(offset)
        .limit(page_size)
    )
    logs = list(rows.scalars().all())
    actor_ids = {log.actor_user_id for log in logs if log.actor_user_id}
    names: dict[uuid.UUID, str] = {}
    if actor_ids:
        users = await db.execute(select(User).where(User.id.in_(actor_ids)))
        names = {u.id: u.full_name for u in users.scalars().all()}

    items = [
        _redact_row(
            log,
            membership,
            names.get(log.actor_user_id) if log.actor_user_id else None,
        )
        for log in logs
    ]
    return items, total
