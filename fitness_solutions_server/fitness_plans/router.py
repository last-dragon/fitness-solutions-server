import functools
from datetime import date, datetime, time, timedelta
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi_pagination import pagination_ctx
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy import and_, func, or_, select, true, update
from sqlalchemy.orm import selectinload, with_expression

from fitness_solutions_server.admins.dependencies import IsAdminDependency
from fitness_solutions_server.collections.models import CollectionItemFitnessPlan
from fitness_solutions_server.core.database import DatabaseDependency
from fitness_solutions_server.core.models import ExperienceLevel, Focus, Sex
from fitness_solutions_server.core.schemas import ResponseModel, SortOrder
from fitness_solutions_server.core.utils import CursorPage, get_or_fail
from fitness_solutions_server.countries.models import Country
from fitness_solutions_server.fitness_coaches.dependencies import (
    GetFitnessCoachDependency,
    RequireFitnessCoachDependency,
)
from fitness_solutions_server.fitness_coaches.mapper import FitnessCoachMapperDependency
from fitness_solutions_server.fitness_coaches.models import FitnessCoach
from fitness_solutions_server.fitness_plans.utils import (
    fitness_plan_model_to_schema,
    fitness_plan_models_to_schema,
    is_saved_expression,
    workout_to_week_status,
)
from fitness_solutions_server.orders.models import Order, OrderStatus, OrderType
from fitness_solutions_server.storage.base import StorageServiceDependency
from fitness_solutions_server.user_workouts.models import UserWorkout
from fitness_solutions_server.users.dependencies import (
    GetUserDependency,
    RequireUserDependency,
)
from fitness_solutions_server.workouts.models import Workout, WorkoutExercise
from fitness_solutions_server.workouts.utils import workout_model_to_schema

from . import models, schemas

router = APIRouter(prefix="/fitness-plans")
FitnessPlanEmbedQuery = Annotated[
    set[schemas.FitnessPlanEmbed] | None, Query(description="Embed relations")
]


@router.post("", summary="Create fitness plan")
async def create(
    body: schemas.FitnessPlanCreate,
    fitness_coach: RequireFitnessCoachDependency,
    db: DatabaseDependency,
    fitness_coach_mapper: FitnessCoachMapperDependency,
    storage_service: StorageServiceDependency,
) -> ResponseModel[schemas.FitnessPlanPrivate]:
    order = await get_or_fail(Order, body.order_id, db)

    if order.fitness_coach_id != fitness_coach.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This order is not for you",
        )
    if order.status != OrderStatus.in_progress:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The order must be in progress",
        )
    if order.type != OrderType.fitness_plan:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The order must be for fitness plans",
        )

    fitness_plan = models.FitnessPlan(
        **body.dict(), fitness_coach_id=fitness_coach.id, order=order
    )

    db.add(fitness_plan)
    await db.commit()

    return ResponseModel(
        data=fitness_plan_model_to_schema(
            is_admin=False,
            auth_fitness_coach_id=fitness_coach.id,
            fitness_plan=fitness_plan,
            fitness_coach_mapper=fitness_coach_mapper,
            storage_service=storage_service,
        )
    )


@router.patch("/{fitness_plan_id}", summary="Update fitness plan")
async def update_fitness_plan(
    fitness_plan_id: UUID,
    body: schemas.FitnessPlanUpdate,
    fitness_coach: GetFitnessCoachDependency,
    is_admin: IsAdminDependency,
    db: DatabaseDependency,
    fitness_coach_mapper: FitnessCoachMapperDependency,
    storage_service: StorageServiceDependency,
) -> ResponseModel[schemas.FitnessPlanPrivate]:
    fitness_plan = await get_or_fail(models.FitnessPlan, fitness_plan_id, db)

    if (
        fitness_coach is not None and fitness_coach.id != fitness_plan.fitness_coach_id
    ) or (fitness_coach is None and not is_admin):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    update_data = body.dict(exclude_unset=True)

    if "name_translations" in update_data:
        fitness_plan.name_translations = update_data["name_translations"]
    if "description_translations" in update_data:
        fitness_plan.description_translations = update_data["description_translations"]
    if "experience_level" in update_data:
        fitness_plan.experience_level = update_data["experience_level"]
    if "number_of_workouts_per_week" in update_data:
        fitness_plan.number_of_workouts_per_week = update_data[
            "number_of_workouts_per_week"
        ]
    if "focus" in update_data:
        fitness_plan.focus = update_data["focus"]
    if "target_sex" in update_data:
        fitness_plan.target_sex = update_data["target_sex"]
    if "min_age" in update_data:
        fitness_plan.min_age = update_data["min_age"]
    if "max_age" in update_data:
        fitness_plan.max_age = update_data["max_age"]
    if body.is_released is not None and is_admin:
        fitness_plan.is_released = body.is_released

    await db.commit()

    return ResponseModel(
        data=fitness_plan_model_to_schema(
            is_admin=is_admin,
            auth_fitness_coach_id=fitness_coach.id
            if fitness_coach is not None
            else None,
            fitness_plan=fitness_plan,
            fitness_coach_mapper=fitness_coach_mapper,
            storage_service=storage_service,
        )
    )


@router.get("/active", summary="Get active fitness plan")
async def get_active(
    user: RequireUserDependency,
    db: DatabaseDependency,
    storage_service: StorageServiceDependency,
    fitness_coach_mapper: FitnessCoachMapperDependency,
    embed: FitnessPlanEmbedQuery = None,
) -> ResponseModel[schemas.FitnessPlanActive | None]:
    query = (
        select(models.FitnessPlan, UserWorkout, models.UserFitnessPlanParticipation.id)
        .join(
            models.UserFitnessPlanParticipation,
            and_(
                models.FitnessPlan.id
                == models.UserFitnessPlanParticipation.fitness_plan_id,
                models.UserFitnessPlanParticipation.user_id == user.id,
            ),
        )
        .join(
            UserWorkout,
            and_(
                models.UserFitnessPlanParticipation.id
                == UserWorkout.fitness_plan_participation_id,
                func.date_trunc("day", UserWorkout.started_at) == date.today(),
            ),
            isouter=True,
        )
        .where(models.UserFitnessPlanParticipation.is_active == true())
        .limit(1)
        .options(
            selectinload(UserWorkout.workout)
            .selectinload(Workout.workout_exercises)
            .selectinload(WorkoutExercise.exercise),
            selectinload(UserWorkout.workout)
            .selectinload(Workout.workout_exercises)
            .selectinload(WorkoutExercise.sets),
        )
    )

    if embed is not None:
        if schemas.FitnessPlanEmbed.fitness_coach in embed:
            query = query.options(selectinload(models.FitnessPlan.fitness_coach))
        if schemas.FitnessPlanEmbed.muscle_groups in embed:
            query = query.options(selectinload(models.FitnessPlan.muscle_groups))
        if schemas.FitnessPlanEmbed.equipment in embed:
            query = query.options(selectinload(models.FitnessPlan.equipment))

    row = (await db.execute(query)).first()
    print("row.UserWorkout = ", row.UserWorkout)
    print("row2 = ", row[2])
    if row:
        if row[2] is not None:
            # Fetch week status
            today = date.today()
            print("today = ", today)
            start_of_week = datetime.combine(
                today - timedelta(days=today.weekday()), time.min
            )
            print("start_of_week = ", start_of_week)
            end_of_week = datetime.combine(start_of_week + timedelta(days=6), time.max)
            print("end_of_week = ", end_of_week)
            this_week_workouts = (
                await db.scalars(
                    select(UserWorkout)
                    .where(UserWorkout.fitness_plan_participation_id == row[2])
                    .where(UserWorkout.started_at.between(start_of_week, end_of_week))
                )
            ).all()
            print(
                "this_week_workouts = ",
                this_week_workouts[0].fitness_plan_participation_id,
            )
            week_status = schemas.FitnessPlanWeekStatus(
                monday=schemas.WeekStatus.none,
                tuesday=schemas.WeekStatus.none,
                wednesday=schemas.WeekStatus.none,
                thursday=schemas.WeekStatus.none,
                friday=schemas.WeekStatus.none,
                saturday=schemas.WeekStatus.none,
                sunday=schemas.WeekStatus.none,
            )
            for workout in this_week_workouts:
                if workout.started_at.weekday() == 0:  # monday
                    week_status.monday = workout_to_week_status(workout)
                elif workout.started_at.weekday() == 1:  # tuesday
                    week_status.tuesday = workout_to_week_status(workout)
                elif workout.started_at.weekday() == 2:  # wednesday
                    week_status.wednesday = workout_to_week_status(workout)
                elif workout.started_at.weekday() == 3:  # thursday
                    week_status.thursday = workout_to_week_status(workout)
                elif workout.started_at.weekday() == 4:  # friday
                    week_status.friday = workout_to_week_status(workout)
                elif workout.started_at.weekday() == 5:  # saturday
                    week_status.saturday = workout_to_week_status(workout)
                elif workout.started_at.weekday() == 6:  # sunday
                    week_status.sunday = workout_to_week_status(workout)
            print("week_status = ", week_status)
        fitness_plan_schema = fitness_plan_model_to_schema(
            is_admin=False,
            auth_fitness_coach_id=None,
            fitness_plan=row.FitnessPlan,
            fitness_coach_mapper=fitness_coach_mapper,
            storage_service=storage_service,
        )
        active_fitness_plan_schema = schemas.FitnessPlanActive(
            **fitness_plan_schema.dict(),
            week_status=week_status,
            participation_id=row[2],
        )

        if row.UserWorkout is not None:
            # All of this stuff to prevent Pydantic from validating schema...
            workout_schema = workout_model_to_schema(
                is_admin=False,
                is_fitness_coach=False,
                workout=row.UserWorkout.workout,
                storage_service=storage_service,
                fitness_coach_mapper=fitness_coach_mapper,
            )
            row.UserWorkout.workout = None
            active_fitness_plan_schema.todays_workout = schemas.UserWorkout.from_orm(
                row.UserWorkout
            )
            active_fitness_plan_schema.todays_workout.workout = workout_schema
        return ResponseModel(data=active_fitness_plan_schema)
    else:
        return ResponseModel(data=None)


@router.get("/{fitness_plan_id}", summary="Get fitness plan")
async def get(
    fitness_plan_id: UUID,
    is_admin: IsAdminDependency,
    fitness_coach_mapper: FitnessCoachMapperDependency,
    fitness_coach: GetFitnessCoachDependency,
    db: DatabaseDependency,
    storage_service: StorageServiceDependency,
    embed: FitnessPlanEmbedQuery = None,
) -> ResponseModel[schemas.FitnessPlanPrivate | schemas.FitnessPlanPublic]:
    options = []
    if embed is not None:
        if schemas.FitnessPlanEmbed.fitness_coach in embed:
            options.append(selectinload(models.FitnessPlan.fitness_coach))
        if schemas.FitnessPlanEmbed.muscle_groups in embed:
            options.append(selectinload(models.FitnessPlan.muscle_groups))
        if schemas.FitnessPlanEmbed.equipment in embed:
            options.append(selectinload(models.FitnessPlan.equipment))
    fitness_plan = await get_or_fail(
        models.FitnessPlan, fitness_plan_id, db, options=options
    )

    return ResponseModel(
        data=fitness_plan_model_to_schema(
            is_admin=is_admin,
            auth_fitness_coach_id=(
                fitness_coach.id if fitness_coach is not None else None
            ),
            fitness_plan=fitness_plan,
            fitness_coach_mapper=fitness_coach_mapper,
            storage_service=storage_service,
        )
    )


@router.get(
    "", summary="List fitness plans", dependencies=[Depends(pagination_ctx(CursorPage))]
)
async def list(
    db: DatabaseDependency,
    is_admin: IsAdminDependency,
    fitness_coach_mapper: FitnessCoachMapperDependency,
    user: GetUserDependency,
    fitness_coach: GetFitnessCoachDependency,
    storage_service: StorageServiceDependency,
    embed: FitnessPlanEmbedQuery = None,
    order_id: Annotated[UUID | None, Query(description="Filter by order ID")] = None,
    sort_by: Annotated[
        schemas.FitnessPlanSortBy, Query(description="Order results")
    ] = schemas.FitnessPlanSortBy.created_at,
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
    fitness_coach_id: Annotated[
        UUID | None, Query(description="Query for workouts by a fitness coach")
    ] = None,
    experience_level: Annotated[
        ExperienceLevel | None,
        Query(description="Filter for specific experience level"),
    ] = None,
    is_saved: Annotated[
        bool | None,
        Query(description="Filter for saved fitness plans (only for users)"),
    ] = None,
    name: Annotated[
        str | None,
        Query(description="Filter for names that contain the supplied value"),
    ] = None,
    age: Annotated[
        int | None,
        Query(
            description="Can be used to filter for fitness plans for a specific age."
        ),
    ] = None,
    collection_id: Annotated[UUID | None, Query()] = None,
) -> ResponseModel[
    CursorPage[schemas.FitnessPlanPrivate] | CursorPage[schemas.FitnessPlanPublic]
]:
    query = select(models.FitnessPlan)

    match sort_by:
        case schemas.FitnessPlanSortBy.created_at:
            query = query.order_by(
                (
                    models.FitnessPlan.created_at.desc()
                    if sort_order == SortOrder.desc
                    else models.FitnessPlan.created_at.asc()
                ),
                models.FitnessPlan.id,
            )
        case schemas.FitnessPlanSortBy.participants_count:
            query = query.order_by(
                (
                    models.FitnessPlan.participants_count.desc()
                    if sort_order == SortOrder.desc
                    else models.FitnessPlan.participants_count.asc()
                ),
                models.FitnessPlan.id,
            )

    if user is not None:
        is_saved_exp = is_saved_expression(user_id=user.id).label("is_saved")
        query = query.options(
            with_expression(models.FitnessPlan.is_saved, is_saved_exp)
        )
        if is_saved is not None:
            query = query.where(is_saved_exp == is_saved)
        query = query.where(
            models.FitnessPlan.fitness_coach.has(
                FitnessCoach.countries.any(Country.id == user.country_id)
            )
        )

    if embed is not None:
        if schemas.FitnessPlanEmbed.fitness_coach in embed:
            query = query.options(selectinload(models.FitnessPlan.fitness_coach))
        if schemas.FitnessPlanEmbed.muscle_groups in embed:
            query = query.options(selectinload(models.FitnessPlan.muscle_groups))
        if schemas.FitnessPlanEmbed.equipment in embed:
            query = query.options(selectinload(models.FitnessPlan.equipment))
    if order_id is not None and (is_admin or fitness_coach is not None):
        query = query.where(models.FitnessPlan.order_id == order_id)
    if focus is not None:
        query = query.where(models.FitnessPlan.focus.in_(focus))
    if experience_level is not None:
        query = query.where(models.FitnessPlan.experience_level == experience_level)
    if target_sex is not None:
        query = query.where(models.FitnessPlan.target_sex == target_sex)
    if min_age is not None:
        query = query.where(models.FitnessPlan.min_age >= min_age)
    if max_age is not None:
        query = query.where(models.FitnessPlan.max_age <= max_age)
    if fitness_coach_id is not None:
        query = query.filter(models.FitnessPlan.fitness_coach_id == fitness_coach_id)
    if name is not None:
        # Not performant, we should add indexes but hard due to localization.
        query = query.where(models.FitnessPlan.name.ilike(f"%{name}%"))
    if age is not None:
        query = query.where(
            or_(models.FitnessPlan.min_age.is_(None), models.FitnessPlan.min_age <= age)
        ).where(
            or_(models.FitnessPlan.max_age.is_(None), models.FitnessPlan.max_age >= age)
        )

    if collection_id is not None:
        exists_stmt = (
            select(CollectionItemFitnessPlan.id)
            .where(CollectionItemFitnessPlan.fitness_plan_id == models.FitnessPlan.id)
            .exists()
        )
        query = query.where(
            exists_stmt.where(CollectionItemFitnessPlan.collection_id == collection_id)
        )
    else:
        # Allow coaches to see their own
        if fitness_coach is not None:
            query = query.where(models.FitnessPlan.fitness_coach_id == fitness_coach.id)
        elif not is_admin:
            # Users and unauthenticated may be only see released fitness plans
            query = query.where(models.FitnessPlan.is_released == true())

    fitness_plans = await paginate(
        db,
        query,
        transformer=functools.partial(
            fitness_plan_models_to_schema,
            is_admin=is_admin,
            auth_fitness_coach_id=fitness_coach_id
            if fitness_coach is not None
            else None,
            fitness_coach_mapper=fitness_coach_mapper,
            storage_service=storage_service,
        ),
    )

    return ResponseModel(data=fitness_plans)


@router.post("/{fitness_plan_id}/weeks", summary="Create fitness plan week")
async def create_week(
    fitness_plan_id: UUID,
    fitness_coach: RequireFitnessCoachDependency,
    db: DatabaseDependency,
) -> ResponseModel[schemas.FitnessPlanWeek]:
    # Select FOR NO KEY UPDATE to prevent order conflicts
    fitness_plan = await get_or_fail(
        models.FitnessPlan, fitness_plan_id, db, with_for_update={"key_share": True}
    )

    if fitness_plan.is_released:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You can't update a fitness plan that is released!",
        )

    if fitness_plan.fitness_coach_id != fitness_coach.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    next_order_number = (
        await db.scalars(
            select(func.coalesce(func.max(models.FitnessPlanWeek.order), 0))
            .select_from(models.FitnessPlanWeek)
            .where(models.FitnessPlanWeek.fitness_plan_id == fitness_plan_id)
        )
    ).one() + 1
    fitness_plan_week = models.FitnessPlanWeek(order=next_order_number)
    fitness_plan.weeks.append(fitness_plan_week)

    await db.commit()

    return ResponseModel(data=schemas.FitnessPlanWeek.from_orm(fitness_plan_week))


@router.delete("/{fitness_plan_id}/weeks/{week_id}", summary="Delete fitness plan week")
async def delete_week(
    fitness_plan_id: UUID,
    week_id: UUID,
    fitness_coach: RequireFitnessCoachDependency,
    db: DatabaseDependency,
) -> ResponseModel[None]:
    fitness_plan = await get_or_fail(models.FitnessPlan, fitness_plan_id, db)
    week = await get_or_fail(models.FitnessPlanWeek, week_id, db)

    if fitness_plan.is_released:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You can't update a fitness plan that is released!",
        )

    if fitness_plan.fitness_coach_id != fitness_coach.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    await db.delete(week)

    # Update order of larger items
    await db.execute(
        update(models.FitnessPlanWeek)
        .where(models.FitnessPlanWeek.order > week.order)
        .values(order=models.FitnessPlanWeek.order - 1)
    )

    await db.commit()
    return ResponseModel(data=None)


@router.post(
    "/{fitness_plan_id}/weeks/{week_id}/workouts",
    summary="Add workout to fitness plan week",
)
async def create_week_workout(
    fitness_plan_id: UUID,
    week_id: UUID,
    body: schemas.FitnessPlanWeekWorkoutCreate,
    fitness_coach: RequireFitnessCoachDependency,
    db: DatabaseDependency,
) -> ResponseModel[schemas.FitnessPlanWeekWorkout]:
    fitness_plan = await get_or_fail(
        models.FitnessPlan,
        fitness_plan_id,
        db,
    )
    # Lock to prevent order conflicts
    week = await get_or_fail(
        models.FitnessPlanWeek, week_id, db, with_for_update={"key_share": True}
    )

    if fitness_plan.is_released:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You can't update a fitness plan that is released!",
        )

    if fitness_plan.fitness_coach_id != fitness_coach.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    workout = await get_or_fail(Workout, body.workout_id, db)

    next_order_number = (
        await db.scalars(
            select(func.coalesce(func.max(models.FitnessPlanWeekWorkout.order), 0))
            .select_from(models.FitnessPlanWeekWorkout)
            .where(models.FitnessPlanWeekWorkout.fitness_plan_week_id == week_id)
        )
    ).one() + 1
    fitness_plan_week_workout = models.FitnessPlanWeekWorkout(
        order=next_order_number, workout=workout
    )
    week.workout_associations.append(fitness_plan_week_workout)

    await db.commit()

    return ResponseModel(
        data=schemas.FitnessPlanWeekWorkout.from_orm(fitness_plan_week_workout)
    )


@router.delete(
    "/{fitness_plan_id}/weeks/{week_id}/workouts/{fitness_plan_week_workout_id}",
    summary="Delete workout from fitness plan week",
)
async def delete_week_wokrout(
    fitness_plan_id: UUID,
    week_id: UUID,
    fitness_plan_week_workout_id: UUID,
    fitness_coach: RequireFitnessCoachDependency,
    db: DatabaseDependency,
) -> ResponseModel[None]:
    fitness_plan = await get_or_fail(models.FitnessPlan, fitness_plan_id, db)
    fitness_plan_week_workout = await get_or_fail(
        models.FitnessPlanWeekWorkout, fitness_plan_week_workout_id, db
    )

    if fitness_plan.is_released:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You can't update a fitness plan that is released!",
        )

    if fitness_plan.fitness_coach_id != fitness_coach.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    await db.delete(fitness_plan_week_workout)

    # Update order of larger items
    await db.execute(
        update(models.FitnessPlanWeekWorkout)
        .where(models.FitnessPlanWeekWorkout.order > fitness_plan_week_workout.order)
        .values(order=models.FitnessPlanWeekWorkout.order - 1)
    )

    await db.commit()
    return ResponseModel(data=None)
