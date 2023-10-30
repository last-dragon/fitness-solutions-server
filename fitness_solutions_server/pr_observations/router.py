import functools
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi_pagination import pagination_ctx
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy import alias, join, select, true
from sqlalchemy.orm import aliased, selectinload

from fitness_solutions_server.admins.dependencies import IsAdminDependency
from fitness_solutions_server.core.database import DatabaseDependency
from fitness_solutions_server.core.schemas import ResponseModel
from fitness_solutions_server.core.utils import CursorPage, get_or_fail
from fitness_solutions_server.exercises.models import Exercise
from fitness_solutions_server.pr_observations.utils import (
    pr_observation_models_to_schema,
)
from fitness_solutions_server.storage.base import StorageServiceDependency
from fitness_solutions_server.users.dependencies import RequireUserDependency

from . import models, schemas

PRObservationEmbedQuery = Annotated[set[schemas.PRObservationEmbed] | None, Query()]
router = APIRouter(prefix="/pr-observations")


@router.post("", summary="Create PR observation")
async def create_pr_observation(
    create_request: schemas.PRObservationCreate,
    user: RequireUserDependency,
    db: DatabaseDependency,
) -> ResponseModel[schemas.PRObservation]:
    exercise = await get_or_fail(Exercise, create_request.exercise_id, db)
    pr_observation = models.PRObservation(
        user_id=user.id, exercise_id=exercise.id, weight=create_request.weight
    )
    db.add(pr_observation)
    await db.commit()
    return ResponseModel(data=schemas.PRObservation.from_orm(pr_observation))


@router.delete("/{observation_id}", summary="Delete PR observation")
async def delete_pr_observation(
    observation_id: UUID,
    user: RequireUserDependency,
    db: DatabaseDependency,
) -> ResponseModel[None]:
    observation = await get_or_fail(models.PRObservation, observation_id, db)
    if observation.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    await db.delete(observation)
    await db.commit()
    return ResponseModel(data=None)


@router.get("/{observation_id}", summary="Get PR observation")
async def get_pr_observation(
    observation_id: UUID, user: RequireUserDependency, db: DatabaseDependency
) -> ResponseModel[schemas.PRObservation]:
    observation = await get_or_fail(models.PRObservation, observation_id, db)
    if observation.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    return ResponseModel(data=schemas.PRObservation.from_orm(observation))


@router.get(
    "",
    summary="List PR observations",
    dependencies=[Depends(pagination_ctx(CursorPage))],
)
async def list_pr_observation(
    user: RequireUserDependency,
    db: DatabaseDependency,
    is_admin: IsAdminDependency,
    storage_service: StorageServiceDependency,
    exercise_id: Annotated[
        UUID | None, Query(description="Filter for exercise IDs")
    ] = None,
    exercise_ids: Annotated[
        set[UUID] | None,
        Query(
            description="Filter for exercise IDs, only returns the latest PR for each exercise"
        ),
    ] = None,
    embed: PRObservationEmbedQuery = None,
) -> ResponseModel[CursorPage[schemas.PRObservation]]:
    query = (
        select(models.PRObservation)
        .where(models.PRObservation.user_id == user.id)
        .order_by(models.PRObservation.created_at.desc(), models.PRObservation.id)
    )

    if exercise_id is not None:
        query = query.where(models.PRObservation.exercise_id == exercise_id)
    elif exercise_ids is not None:
        distinct_select = (
            select(models.PRObservation.exercise_id.distinct().label("exercise_id"))
            .where(models.PRObservation.user_id == user.id)
            .subquery()
        )
        latest_record_select = (
            select(models.PRObservation)
            .where(models.PRObservation.exercise_id == distinct_select.c.exercise_id)
            .order_by(models.PRObservation.created_at.desc())
            .limit(1)
            .lateral()
        )
        # mypy complains about type, but it works...
        latest_alias = aliased(models.PRObservation, latest_record_select)  # type: ignore

        query = (
            select(latest_alias)
            .select_from(distinct_select)
            .join(latest_alias, onclause=true())
            .order_by(latest_alias.created_at.desc(), latest_alias.id)
        )

    if embed is not None:
        if schemas.PRObservationEmbed.exercise in embed:
            query = query.options(selectinload(models.PRObservation.exercise))

    observations = await paginate(
        db,
        query,
        transformer=functools.partial(
            pr_observation_models_to_schema,
            is_admin=is_admin,
            storage_service=storage_service,
        ),
    )

    return ResponseModel(data=observations)
