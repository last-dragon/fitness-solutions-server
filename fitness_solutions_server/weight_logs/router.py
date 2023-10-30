import datetime
from http.client import HTTPException
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from fastapi_pagination import pagination_ctx
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy import select

from fitness_solutions_server.core.database import DatabaseDependency
from fitness_solutions_server.core.schemas import ResponseModel
from fitness_solutions_server.core.utils import CursorPage, get_or_fail
from fitness_solutions_server.users.dependencies import RequireUserDependency
from fitness_solutions_server.weight_logs import models, schemas
from fitness_solutions_server.weight_logs.models import WeightLog

router = APIRouter(prefix="/weight-logs")


@router.post("", summary="Create weight log")
async def create(
    body: schemas.WeightLogCreate, user: RequireUserDependency, db: DatabaseDependency
) -> ResponseModel[schemas.WeightLog]:
    weight_log = WeightLog(weight=body.weight, user_id=user.id)
    db.add(weight_log)
    await db.commit()
    return ResponseModel(data=schemas.WeightLog.from_orm(weight_log))


@router.delete("/{weight_log_id}", summary="Delete weight log")
async def delete(
    weight_log_id: UUID, user: RequireUserDependency, db: DatabaseDependency
) -> ResponseModel[None]:
    weight_log = await get_or_fail(models.WeightLog, weight_log_id, db)
    if weight_log.user_id != user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN)
    await db.delete(weight_log)
    await db.commit()
    return ResponseModel()


@router.get(
    "", summary="List weight logs", dependencies=[Depends(pagination_ctx(CursorPage))]
)
async def list(
    user: RequireUserDependency,
    db: DatabaseDependency,
    created_at_gte: Annotated[
        datetime.datetime | None,
        Query(description="Filter for `created_at` greather than or equal to"),
    ] = None,
    created_at_lte: Annotated[
        datetime.datetime | None,
        Query(description="Filter for `created_at` less than or equal to"),
    ] = None,
) -> ResponseModel[CursorPage[schemas.WeightLog]]:
    query = (
        select(models.WeightLog)
        .where(models.WeightLog.user_id == user.id)
        .order_by(models.WeightLog.created_at.desc(), models.WeightLog.id)
    )
    if created_at_gte is not None:
        query = query.where(models.WeightLog.created_at >= created_at_gte)
    if created_at_lte is not None:
        query = query.where(models.WeightLog.created_at <= created_at_lte)

    weight_logs = await paginate(db, query)
    return ResponseModel(data=weight_logs)
