import functools
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Query, status
from fastapi_pagination import pagination_ctx
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy import case, select, true
from sqlalchemy.orm import aliased, selectinload

from fitness_solutions_server.admins.dependencies import (
    IsAdminDependency,
    require_admin_authentication_token,
)
from fitness_solutions_server.core.database import DatabaseDependency
from fitness_solutions_server.core.schemas import ResponseModel
from fitness_solutions_server.core.utils import (
    CursorPage,
    get_or_fail,
    get_or_fail_many,
)
from fitness_solutions_server.equipment.models import Equipment
from fitness_solutions_server.exercises.utils import (
    exercise_model_to_schema,
    exercises_models_to_schema,
    make_exercises_image_path,
)
from fitness_solutions_server.images.models import Image
from fitness_solutions_server.muscle_groups.models import MuscleGroup
from fitness_solutions_server.pr_observations.models import PRObservation
from fitness_solutions_server.storage.base import StorageServiceDependency
from fitness_solutions_server.users.dependencies import GetUserDependency

from . import models, schemas

ExerciseEmbedQuery = Annotated[set[schemas.ExerciseEmbed] | None, Query()]
router = APIRouter(prefix="/exercises")


@router.post(
    "",
    summary="Create exercise",
    dependencies=[Depends(require_admin_authentication_token)],
    status_code=status.HTTP_201_CREATED,
)
async def create(
    create_request: schemas.ExerciseCreate,
    db: DatabaseDependency,
    storage_service: StorageServiceDependency,
) -> ResponseModel[schemas.ExerciseAdmin]:
    image = await get_or_fail(Image, create_request.image_id, db)

    equipment = await get_or_fail_many(Equipment, create_request.equipment_ids, db)

    muscle_groups = await get_or_fail_many(
        MuscleGroup, create_request.muscle_groups_ids, db
    )

    exercise_id = uuid4()
    exercise_image_path = make_exercises_image_path(id=exercise_id, image=image)
    exercise = models.Exercise(
        id=exercise_id,
        name_translations=create_request.name_translations,
        en_name=create_request.en_name,
        is_bodyweight=create_request.is_bodyweight,
        image_path=exercise_image_path,
        muscle_groups=muscle_groups,
        equipment=equipment,
        model_3d_path=str(create_request.model_3d_path),
    )
    db.add(exercise)
    await db.flush()

    # Move image
    # await storage_service.move(from_path=image.path, to_path=exercise_image_path)
    await db.delete(image)

    await db.commit()

    return ResponseModel(
        data=exercise_model_to_schema(
            is_admin=True, exercise=exercise, storage_service=storage_service
        )
    )


@router.get("/{exercise_id}", summary="Get exercise by ID")
async def get(
    exercise_id: UUID,
    db: DatabaseDependency,
    storage_service: StorageServiceDependency,
    is_admin: IsAdminDependency,
) -> ResponseModel[schemas.ExerciseAdmin | schemas.Exercise]:
    exercise = await get_or_fail(models.Exercise, exercise_id, db)
    return ResponseModel(
        data=exercise_model_to_schema(
            is_admin=is_admin, exercise=exercise, storage_service=storage_service
        )
    )


@router.get(
    "", summary="List exercises", dependencies=[Depends(pagination_ctx(CursorPage))]
)
async def list(
    db: DatabaseDependency,
    storage_service: StorageServiceDependency,
    is_admin: IsAdminDependency,
    user: GetUserDependency,
    order_by: schemas.ExerciseListOrderBy = schemas.ExerciseListOrderBy.id,
    muscle_groups_one_of: Annotated[
        set[UUID] | None,
        Query(
            description=(
                "Filter by exercises that contain"
                " at least one of the muscle groups provided"
            ),
        ),
    ] = None,
    name: Annotated[
        str | None,
        Query(description="Search for a name", min_length=1),
    ] = None,
    embed: ExerciseEmbedQuery = None,
) -> ResponseModel[CursorPage[schemas.ExerciseAdmin] | CursorPage[schemas.Exercise]]:
    query = (
        select(models.Exercise)
        .options(
            selectinload(models.Exercise.muscle_groups),
            selectinload(models.Exercise.equipment),
        )
        .select_from(models.Exercise)
    )

    if embed is not None:
        if schemas.ExerciseEmbed.latest_personal_record in embed and user is not None:
            select_personal_record_statement = (
                select(PRObservation)
                .where(PRObservation.user_id == user.id)
                .where(PRObservation.exercise_id == models.Exercise.id)
                .order_by(PRObservation.created_at.desc())
                .limit(1)
                .lateral()
            )
            personal_record_alias = aliased(
                PRObservation, select_personal_record_statement
            )
            query = query.add_columns(personal_record_alias).join(
                personal_record_alias,
                onclause=true(),
                isouter=True,
            )

    # Filtering

    # Performance can maybe be improved by manually using EXISTS
    # instead of `any`, since it also joins `muscle_groups`
    if muscle_groups_one_of is not None:
        query = query.where(
            models.Exercise.muscle_groups.any(MuscleGroup.id.in_(muscle_groups_one_of))
        )

    # Not performant, we should add indexes but hard due to localization.
    if name is not None:
        query = query.where(models.Exercise.name.ilike(f"%{name}%"))

    # Ordering
    match order_by:
        case schemas.ExerciseListOrderBy.muscle_group:
            # Create CTE selects a single muscle group name for each exercise
            # NOTE: If the exercies does not have any muscle groups,
            # it will be excluded from the results.
            muscle_group_cte = (
                select(
                    models.exercise_muscle_groups.c.exercise_id,
                    MuscleGroup.body_part,
                    MuscleGroup.name.label("name"),
                )
                .distinct(models.exercise_muscle_groups.c.exercise_id)
                .join(
                    MuscleGroup,
                    models.exercise_muscle_groups.c.muscle_group_id == MuscleGroup.id,
                )
                .order_by(
                    models.exercise_muscle_groups.c.exercise_id,
                    case(
                        models.body_part_ordering, value=MuscleGroup.body_part, else_=99
                    ),
                    MuscleGroup.name,
                )
                .cte()
            )
            query = query.outerjoin(
                muscle_group_cte,
                models.Exercise.id == muscle_group_cte.c.exercise_id,
            ).order_by(
                case(
                    models.body_part_ordering,
                    value=muscle_group_cte.c.body_part,
                    else_=99,
                ),
                muscle_group_cte.c.name,
                models.Exercise.id,
            )
        case schemas.ExerciseListOrderBy.id:
            query = query.order_by(models.Exercise.id)

    exercises = await paginate(
        db,
        query,
        transformer=functools.partial(
            exercises_models_to_schema,
            is_admin=is_admin,
            storage_service=storage_service,
        ),
    )

    return ResponseModel(data=exercises)


@router.delete(
    "/{exercise_id}",
    summary="Delete exercise",
    dependencies=[Depends(require_admin_authentication_token)],
)
async def delete(exercise_id: UUID, db: DatabaseDependency) -> ResponseModel[None]:
    exercise = await get_or_fail(models.Exercise, exercise_id, db)
    exercise.delete()
    await db.commit()

    return ResponseModel(data=None)


@router.patch(
    "/{exercise_id}",
    summary="Update exercise",
    dependencies=[Depends(require_admin_authentication_token)],
)
async def update(
    exercise_id: UUID,
    exercise_update: schemas.ExerciseUpdate,
    db: DatabaseDependency,
    storage_service: StorageServiceDependency,
) -> ResponseModel[schemas.ExerciseAdmin]:
    exercise = await get_or_fail(models.Exercise, exercise_id, db)

    if exercise_update.is_bodyweight is not None:
        exercise.is_bodyweight = exercise_update.is_bodyweight
    if exercise_update.relative_bodyweight_intensity is not None:
        exercise.relative_bodyweight_intensity = exercise.relative_bodyweight_intensity
    if exercise_update.en_name is not None:
        exercise.en_name = exercise_update.en_name
    if exercise_update.model_3d_path is not None:
        exercise.model_3d_path = str(exercise_update.model_3d_path)

    if exercise_update.name_translations is not None:
        exercise.name_translations = exercise_update.name_translations

    if exercise_update.muscle_groups_ids is not None:
        exercise.muscle_groups = await get_or_fail_many(
            MuscleGroup, exercise_update.muscle_groups_ids, db
        )

    if exercise_update.equipment_ids is not None:
        exercise.equipment = await get_or_fail_many(
            Equipment, exercise_update.equipment_ids, db
        )

    if exercise_update.image_id is not None:
        image = await get_or_fail(Image, exercise_update.image_id, db)
        exercise.image_path = make_exercises_image_path(id=exercise_id, image=image)
        await storage_service.move(from_path=image.path, to_path=exercise.image_path)
        await db.delete(image)

    await db.commit()

    return ResponseModel(
        data=exercise_model_to_schema(
            is_admin=True, exercise=exercise, storage_service=storage_service
        )
    )
