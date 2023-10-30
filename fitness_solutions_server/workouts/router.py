import functools
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi_pagination import pagination_ctx
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy import delete, or_, select, true
from sqlalchemy.orm import with_expression

from fitness_solutions_server.admins.dependencies import IsAdminDependency
from fitness_solutions_server.collections.models import CollectionItemWorkout
from fitness_solutions_server.core.database import DatabaseDependency
from fitness_solutions_server.core.models import ExperienceLevel, Focus, Sex
from fitness_solutions_server.core.schemas import ResponseModel, SortOrder
from fitness_solutions_server.core.utils import (
    CursorPage,
    get_or_fail,
    get_or_fail_many,
)
from fitness_solutions_server.countries.models import Country
from fitness_solutions_server.equipment.models import Equipment
from fitness_solutions_server.exercises.models import Exercise
from fitness_solutions_server.fitness_coaches.dependencies import (
    GetFitnessCoachDependency,
    IsFitnessCoachDependency,
)
from fitness_solutions_server.fitness_coaches.mapper import FitnessCoachMapperDependency
from fitness_solutions_server.fitness_coaches.models import FitnessCoach
from fitness_solutions_server.muscle_groups.models import MuscleGroup
from fitness_solutions_server.orders.models import Order, OrderType
from fitness_solutions_server.storage.base import StorageServiceDependency
from fitness_solutions_server.users.dependencies import GetUserDependency
from fitness_solutions_server.workouts import models, schemas
from fitness_solutions_server.workouts.exceptions import OrderNotForYou
from fitness_solutions_server.workouts.utils import (
    is_saved_expression,
    options_for_embeds,
    workout_model_to_schema,
    workout_models_to_schema,
)

router = APIRouter(prefix="/workouts")
WorkoutEmbedQuery = Annotated[
    set[schemas.WorkoutEmbedOption] | None, Query(description="Embed relations")
]


@router.post("", summary="Create workout")
async def create(
    create_request: schemas.WorkoutCreate,
    fitness_coach: GetFitnessCoachDependency,
    db: DatabaseDependency,
    is_admin: IsAdminDependency,
    storage_service: StorageServiceDependency,
    user: GetUserDependency,
    fitness_coach_mapper: FitnessCoachMapperDependency,
    is_fitness_coach: IsFitnessCoachDependency,
) -> ResponseModel[schemas.WorkoutPrivate | schemas.Workout]:
    workout = models.Workout(
        name_translations=create_request.name_translations,
        description_translations=create_request.description_translations,
        experience_level=create_request.experience_level,
        # duration=sum(
        #     [s.duration or 0 for ex in create_request.exercises for s in ex.sets]
        # ),
    )

    if fitness_coach is not None:
        if create_request.order_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You must supply an order ID.",
            )
        order = await get_or_fail(Order, create_request.order_id, db)
        if order.fitness_coach_id != fitness_coach.id:
            raise OrderNotForYou()
        if order.type != OrderType.workout:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The order must be for workouts",
            )
        workout.order = order
        workout.fitness_coach_id = fitness_coach.id
        workout.is_released = False
        workout.focus = create_request.focus
        workout.target_sex = create_request.target_sex
        workout.min_age = create_request.min_age
        workout.max_age = create_request.max_age
    elif user is not None:
        workout.user = user
        workout.is_released = True
    else:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    exercises = await get_or_fail_many(
        models.Exercise, set([e.exercise_id for e in create_request.exercises]), db
    )
    db.add(workout)

    for idx, e in enumerate(create_request.exercises):
        exercise = next(filter(lambda el: el.id == e.exercise_id, exercises))
        workout.workout_exercises.append(
            models.WorkoutExercise(
                exercise=exercise,
                order=idx + 1,
                sets=[
                    models.WorkoutExerciseSet(**s.dict(), order=set_idx + 1)
                    for set_idx, s in enumerate(e.sets)
                ],
            )
        )

    await db.commit()

    return ResponseModel(
        data=workout_model_to_schema(
            is_admin=is_admin,
            is_fitness_coach=is_fitness_coach,
            workout=workout,
            storage_service=storage_service,
            fitness_coach_mapper=fitness_coach_mapper,
        )
    )


@router.get("/{workout_id}", summary="Get workout by ID")
async def get_by_id(
    workout_id: UUID,
    db: DatabaseDependency,
    is_admin: IsAdminDependency,
    storage_service: StorageServiceDependency,
    fitness_coach: GetFitnessCoachDependency,
    fitness_coach_mapper: FitnessCoachMapperDependency,
    user: GetUserDependency,
    is_fitness_coach: IsFitnessCoachDependency,
    embed: WorkoutEmbedQuery = None,
) -> ResponseModel[schemas.WorkoutPrivate | schemas.Workout]:
    options = options_for_embeds(embed)

    if user is not None:
        options.append(
            with_expression(
                models.Workout.is_saved, is_saved_expression(user_id=user.id)
            )
        )

    workout = await get_or_fail(models.Workout, workout_id, db, options=options)

    # TODO: Check it is released for users
    # Check authentication
    if fitness_coach is not None and workout.fitness_coach_id != fitness_coach.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    elif not is_admin and user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    return ResponseModel(
        data=workout_model_to_schema(
            is_admin=is_admin,
            is_fitness_coach=is_fitness_coach,
            workout=workout,
            storage_service=storage_service,
            fitness_coach_mapper=fitness_coach_mapper,
        )
    )


@router.get(
    "", summary="List workouts", dependencies=[Depends(pagination_ctx(CursorPage))]
)
async def list(
    db: DatabaseDependency,
    is_admin: IsAdminDependency,
    user: GetUserDependency,
    fitness_coach: GetFitnessCoachDependency,
    storage_service: StorageServiceDependency,
    fitness_coach_mapper: FitnessCoachMapperDependency,
    is_fitness_coach: IsFitnessCoachDependency,
    embed: WorkoutEmbedQuery = None,
    order_id: Annotated[UUID | None, Query(description="Filter by order ID")] = None,
    sort_by: Annotated[
        schemas.WorkoutSortBy, Query(description="Order results")
    ] = schemas.WorkoutSortBy.created_at,
    sort_order: SortOrder = SortOrder.desc,
    focus: Annotated[
        set[Focus] | None, Query(description="Filter for specific focuses")
    ] = None,
    target_sex: Annotated[
        Sex | None, Query(description="Filter for specific target sex")
    ] = None,
    min_age: Annotated[
        int | None, Query(description="Lower bound (inclusive) for age")
    ] = None,
    max_age: Annotated[
        int | None, Query(description="Upper bound (inclusive) for age")
    ] = None,
    muscle_groups_one_of: Annotated[
        set[UUID] | None,
        Query(description="Filter for workouts that contain one of the muscle groups"),
    ] = None,
    min_duration: Annotated[
        int | None, Query(description="Lower bound (inclusive) for duration")
    ] = None,
    max_duration: Annotated[
        int | None, Query(description="Upper bound (inclusive) for duration")
    ] = None,
    equipment_one_of: Annotated[
        set[UUID] | None,
        Query(description="Filter for workouts that contain one of the equipment"),
    ] = None,
    fitness_coach_id: Annotated[
        UUID | None, Query(description="Query for workouts by a fitness coach")
    ] = None,
    is_saved: Annotated[
        bool | None, Query(description="Filter for saved workouts (only for users)")
    ] = None,
    name: Annotated[
        str | None,
        Query(description="Filter for names that contain the supplied value"),
    ] = None,
    age: Annotated[
        int | None,
        Query(description="Can be used to filter for workouts for a specific age."),
    ] = None,
    user_id: Annotated[
        UUID | None,
        Query(
            description="Query for user ID (only available for current user and admins)"
        ),
    ] = None,
    fitness_plan_id: Annotated[
        UUID | None, Query(description="Filter for workouts included in a fitness plan")
    ] = None,
    collection_id: Annotated[UUID | None, Query()] = None,
    experience_levels: Annotated[set[ExperienceLevel] | None, Query()] = None,
) -> ResponseModel[CursorPage[schemas.WorkoutPrivate] | CursorPage[schemas.Workout]]:
    query = select(models.Workout).options(*options_for_embeds(embed))

    match sort_by:
        case schemas.WorkoutSortBy.created_at:
            query = query.order_by(
                (
                    models.Workout.created_at.desc()
                    if sort_order == SortOrder.desc
                    else models.Workout.created_at.asc()
                ),
                models.Workout.id,
            )
        case schemas.WorkoutSortBy.completed_count:
            query = query.order_by(
                (
                    models.Workout.completed_count.desc()
                    if sort_order == SortOrder.desc
                    else models.Workout.completed_count.asc()
                ),
                models.Workout.id,
            )

    if user is not None:
        is_saved_exp = is_saved_expression(user_id=user.id).label("is_saved")
        query = query.options(with_expression(models.Workout.is_saved, is_saved_exp))
        if is_saved is not None:
            query = query.where(is_saved_exp == is_saved)
        query = query.where(
            or_(
                models.Workout.fitness_coach.has(
                    FitnessCoach.countries.any(Country.id == user.country_id)
                ),
                models.Workout.user_id == user.id,
            )
        )

    if user_id is not None and (is_admin or (user is not None and user.id == user_id)):
        query = query.where(models.Workout.user_id == user_id)
    if order_id is not None and (is_admin or is_fitness_coach):
        query = query.where(models.Workout.order_id == order_id)
    if focus is not None:
        query = query.where(models.Workout.focus.in_(focus))
    if target_sex is not None:
        query = query.where(models.Workout.target_sex == target_sex)
    if min_age is not None:
        query = query.where(models.Workout.min_age >= min_age)
    if max_age is not None:
        query = query.where(models.Workout.max_age <= max_age)
    if muscle_groups_one_of is not None:
        # Can perhaps be optimized, we don't need the muscle group and exercise tables
        # only the association tables.
        query = query.where(
            models.Workout.exercises.any(
                Exercise.muscle_groups.any(MuscleGroup.id.in_(muscle_groups_one_of))
            )
        )
    if min_duration is not None:
        query = query.filter(models.Workout.duration >= min_duration)
    if max_duration is not None:
        query = query.filter(models.Workout.duration <= max_duration)
    if equipment_one_of is not None:
        # Can perhaps be optimized, we don't need the muscle group and exercise tables
        # only the association tables.
        query = query.where(
            models.Workout.exercises.any(
                Exercise.equipment.any(Equipment.id.in_(equipment_one_of))
            )
        )
    if fitness_coach_id is not None:
        query = query.filter(models.Workout.fitness_coach_id == fitness_coach_id)
    if name is not None:
        # Not performant, we should add indexes but hard due to localization.
        query = query.where(models.Workout.name.ilike(f"%{name}%"))
    if age is not None:
        query = query.where(
            or_(models.Workout.min_age.is_(None), models.Workout.min_age <= age)
        ).where(or_(models.Workout.max_age.is_(None), models.Workout.max_age >= age))
    if fitness_plan_id is not None:
        query = query.where(models.Workout.fitness_plans.any(id=fitness_plan_id))
    if experience_levels is not None:
        query = query.where(models.Workout.experience_level.in_(experience_levels))

    # Only allow users to see workouts that are not in collection
    exists_stmt = (
        select(CollectionItemWorkout.id)
        .where(CollectionItemWorkout.workout_id == models.Workout.id)
        .exists()
    )
    if collection_id is not None:
        query = query.where(
            exists_stmt.where(CollectionItemWorkout.collection_id == collection_id)
        )
    else:
        if fitness_coach is not None:
            # Fitness coaches can only see their own workouts
            query = query.where(models.Workout.fitness_coach_id == fitness_coach.id)
        elif user is not None:
            # Users can see public workouts and their own
            query = query.where(
                or_(
                    models.Workout.user_id == user.id,
                    models.Workout.is_released == true(),
                )
            )
        elif not is_admin:
            # Unauthenticated can only see released workouts
            query = query.where(models.Workout.is_released == true())

    workouts = await paginate(
        db,
        query,
        transformer=functools.partial(
            workout_models_to_schema,
            is_admin=is_admin,
            is_fitness_coach=is_fitness_coach,
            storage_service=storage_service,
            fitness_coach_mapper=fitness_coach_mapper,
        ),
    )

    return ResponseModel(data=workouts)


@router.patch(
    "/{workout_id}",
    summary="Update workout",
)
async def update(
    workout_id: UUID,
    workout_update: schemas.WorkoutUpdate,
    db: DatabaseDependency,
    fitness_coach: GetFitnessCoachDependency,
    is_fitness_coach: IsFitnessCoachDependency,
    is_admin: IsAdminDependency,
    storage_service: StorageServiceDependency,
    fitness_coach_mapper: FitnessCoachMapperDependency,
) -> ResponseModel[schemas.WorkoutPrivate]:
    workout = await get_or_fail(models.Workout, workout_id, db)

    if (
        not is_admin
        and (fitness_coach is not None and fitness_coach.id != workout.fitness_coach_id)
    ) or (not is_admin and fitness_coach is None):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    if workout_update.is_released is not None and is_admin:
        if workout.fitness_coach_id is not None:
            fitness_coach = await get_or_fail(
                FitnessCoach, workout.fitness_coach_id, db
            )
            if not fitness_coach.is_released and workout_update.is_released:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Can't release a workout for an unreleased coach",
                )

        workout.is_released = workout_update.is_released
    if workout_update.name_translations is not None:
        workout.name_translations = workout_update.name_translations
    if workout_update.description_translations is not None:
        workout.description_translations = workout_update.description_translations
    if workout_update.experience_level is not None:
        workout.experience_level = workout_update.experience_level
    if workout_update.exercises is not None:
        exercises = await get_or_fail_many(
            models.Exercise, set([e.exercise_id for e in workout_update.exercises]), db
        )

        workout_exercises = []
        for idx, e in enumerate(workout_update.exercises):
            exercise = next(filter(lambda el: el.id == e.exercise_id, exercises))
            workout_exercises.append(
                models.WorkoutExercise(
                    exercise=exercise,
                    order=idx + 1,
                    sets=[
                        models.WorkoutExerciseSet(**s.dict(), order=set_idx + 1)
                        for set_idx, s in enumerate(e.sets)
                    ],
                )
            )
        await db.execute(
            delete(models.WorkoutExercise).where(
                models.WorkoutExercise.workout_id == workout.id
            )
        )
        workout.workout_exercises = workout_exercises

    await db.commit()

    return ResponseModel(
        data=workout_model_to_schema(
            is_admin=is_admin,
            is_fitness_coach=is_fitness_coach,
            workout=workout,
            storage_service=storage_service,
            fitness_coach_mapper=fitness_coach_mapper,
        )
    )


# @router.delete("/{workout_id}/exercises/{workout_exercise_id}")
# async def delete_workout_exercise(
#     workout_id: UUID, workout_exercise_id: UUID, db: DatabaseDependency
# ) -> ResponseModel[None]:
#     workout = await get_or_fail(models.Workout, workout_id, db)
#     workout_exercise = await get_or_fail(
#         models.WorkoutExercise, workout_exercise_id, db
#     )
