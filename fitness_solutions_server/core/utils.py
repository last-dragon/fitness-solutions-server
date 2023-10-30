from typing import Any, Sequence, Type, TypeVar, cast

from fastapi import HTTPException, Query, status
from fastapi_pagination.cursor import CursorPage
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import noload
from sqlalchemy.orm.interfaces import ORMOption
from sqlalchemy.sql.selectable import ForUpdateParameter

ModelType = TypeVar("ModelType", bound=Any)


CursorPage = CursorPage.with_custom_options(  # type: ignore
    size=Query(10, ge=0, le=100, description="Page offset")
)


async def get_or_fail(
    model: Type[ModelType],
    id: Any,
    db: AsyncSession,
    options: Sequence[ORMOption] | None = None,
    with_for_update: ForUpdateParameter = None,
) -> ModelType:
    entity = await db.get(model, id, options=options, with_for_update=with_for_update)
    if entity is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"{model} not found"
        )

    return entity


async def get_or_fail_many(
    model: Type[ModelType], ids: set[Any], db: AsyncSession
) -> list[ModelType]:
    if len(ids) == 0:
        return []
    entities = (
        await db.scalars(select(model).where(model.id.in_(ids)).options(noload("*")))
    ).all()
    not_found = set(ids) - set([e.id for e in entities])
    if len(not_found) != 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{model} with IDs: {', '.join(map(str, not_found))} not found",
        )

    return cast(list[ModelType], entities)
