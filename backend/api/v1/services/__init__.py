from typing import Any

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession


async def paginate(
    session: AsyncSession,
    query: Select[Any],
    limit: int,
    offset: int,
) -> tuple[list[Any], int]:
    total_result = await session.execute(
        select(func.count()).select_from(query.subquery())
    )
    total = total_result.scalar_one()

    result = await session.execute(query.limit(limit).offset(offset))
    rows = list(result.scalars().all())

    return rows, total
