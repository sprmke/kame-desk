from sqlalchemy import Select, asc, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import ColumnElement

PAGE_SIZES = (25, 50, 100)
DEFAULT_PAGE_SIZE = 25
MAX_PAGE_SIZE = 100


def clamp_page(page: int | None) -> int:
    if page is None or page < 1:
        return 1
    return page


def clamp_page_size(
    page_size: int | None,
    *,
    default: int = DEFAULT_PAGE_SIZE,
    max_size: int = MAX_PAGE_SIZE,
) -> int:
    if page_size is None:
        return default
    return min(max(int(page_size), 1), max_size)


def parse_sort(
    sort: str | None,
    allowed: dict[str, ColumnElement],
    default_key: str,
    default_dir: str = "asc",
) -> ColumnElement:
    key = default_key
    direction = default_dir
    if sort:
        parts = sort.split(":", 1)
        if parts[0] in allowed:
            key = parts[0]
        if len(parts) > 1 and parts[1] in ("asc", "desc"):
            direction = parts[1]
    column = allowed[key]
    return desc(column) if direction == "desc" else asc(column)


async def paginate(
    db: AsyncSession,
    query: Select,
    page: int,
    page_size: int,
) -> tuple[list, int]:
    page = clamp_page(page)
    page_size = clamp_page_size(page_size)
    count_stmt = select(func.count()).select_from(query.order_by(None).subquery())
    total = int(await db.scalar(count_stmt) or 0)
    result = await db.execute(query.offset((page - 1) * page_size).limit(page_size))
    return list(result.scalars().unique().all()), total
