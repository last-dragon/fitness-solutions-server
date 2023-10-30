import datetime
from collections import deque
from itertools import cycle
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import insert, select, update

from fitness_solutions_server.core.database import DatabaseDependency
from fitness_solutions_server.core.schemas import ResponseModel
from fitness_solutions_server.core.utils import get_or_fail
from fitness_solutions_server.fitness_plans.utils import leave_fitness_plan
from fitness_solutions_server.user_workouts.models import UserWorkout
from fitness_solutions_server.users.dependencies import RequireUserDependency

from . import models, schemas

router = APIRouter(prefix="/fitness-plan-participations")


@router.post("", summary="Join fitness plan")
async def join_fitness_plan(
    body: schemas.FitnessPlanParticipationCreate,
    user: RequireUserDependency,
    db: DatabaseDependency,
) -> ResponseModel[schemas.FitnessPlanParticipation]:
    # Fetch fitness plan
    fitness_plan = await get_or_fail(models.FitnessPlan, body.fitness_plan_id, db)

    if len(set(body.days)) != fitness_plan.number_of_workouts_per_week:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"You need to choose {fitness_plan.number_of_workouts_per_week} days.",
        )

    # Get the date the fitness plan starts
    current_date = datetime.date.today()
    sorted_days_chosen = sorted(body.days)
    # Choose the next day possible day to start
    start_day = next(
        filter(
            lambda day: day.numeric_value() >= current_date.weekday(),
            sorted_days_chosen,
        ),
        None,
    )
    # If we can't choose a future nearest day, select the first day chosen of next week.
    if start_day is None:
        start_day = sorted_days_chosen[0]
    days_until_start = (start_day.numeric_value() - current_date.weekday()) % 7
    start_date = current_date + datetime.timedelta(days=days_until_start)

    # Set current participation (if any) as inactive
    participations_left = await db.scalars(
        update(models.UserFitnessPlanParticipation)
        .where(models.UserFitnessPlanParticipation.user_id == user.id)
        .where(models.UserFitnessPlanParticipation.fitness_plan_id == fitness_plan.id)
        .values(is_active=False)
        .returning(models.UserFitnessPlanParticipation.id)
    )

    for participation_id in participations_left:
        await leave_fitness_plan(participation_id=participation_id, db=db)

    # Create participation object
    participation = models.UserFitnessPlanParticipation(
        user_id=user.id,
        fitness_plan_id=fitness_plan.id,
        started_at=start_date,
        is_active=True,
    )
    db.add(participation)
    await db.flush()  # Flush to make sure participation ID is populated

    # Create planned workouts
    workouts = (
        await db.scalars(
            select(models.FitnessPlanWeekWorkout.workout_id)
            .join(models.FitnessPlanWeekWorkout.fitness_plan_week)
            .where(models.FitnessPlanWeek.fitness_plan_id == fitness_plan.id)
            .order_by(
                models.FitnessPlanWeek.order.asc(),
                models.FitnessPlanWeekWorkout.order.asc(),
            )
        )
    ).all()
    # Generate insert statements for future workouts for each day.
    shifted_days = deque(sorted_days_chosen)
    shifted_days.rotate(-sorted_days_chosen.index(start_day))

    planned_workouts = []
    temp_date = start_date
    for workout_id, workout_day in zip(workouts, cycle(shifted_days)):
        days_until_next = (workout_day.numeric_value() - temp_date.weekday()) % 7
        temp_date = temp_date + datetime.timedelta(days=days_until_next)
        planned_workouts.append(
            {
                "id": uuid4(),
                "workout_id": workout_id,
                "user_id": user.id,
                "fitness_plan_participation_id": participation.id,
                "started_at": temp_date,
            }
        )

    await db.execute(insert(UserWorkout).values(planned_workouts))

    # for idx, day in enumerate(shifted_days):
    #     select_stmt = (
    #         # Maybe we can simplify this to one insert statement instead of per weekday
    #         select(
    #             label("id", func.gen_random_uuid()),
    #             label("user_id", literal(user.id)),
    #             models.FitnessPlanWeekWorkout.workout_id,
    #             label("fitness_plan_participation_id", literal(participation.id)),
    #             func.cast(
    #                 func.date_trunc(
    #                     "week",
    #                     start_date
    #                     + datetime.timedelta(weeks=1)
    #                     * (models.FitnessPlanWeek.order - 1),
    #                 ),
    #                 Date,
    #             )
    #             + day.numeric_value(),
    #         )
    #         .select_from(models.FitnessPlanWeekWorkout)
    #         .join(models.FitnessPlanWeekWorkout.fitness_plan_week)
    #         .where(models.FitnessPlanWeekWorkout.order == idx + 1)
    #     )
    #     await db.execute(
    #         insert(UserWorkout).from_select(
    #             [
    #                 "id",
    #                 "user_id",
    #                 "workout_id",
    #                 "fitness_plan_participation_id",
    #                 "started_at",
    #             ],
    #             select_stmt,
    #         )
    #     )

    # Commit
    await db.commit()

    # Return object
    return ResponseModel(data=schemas.FitnessPlanParticipation.from_orm(participation))


@router.patch("/{participation_id}", summary="Update fitness plan participation")
async def update_participation(
    participation_id: UUID,
    body: schemas.FitnessPlanParticipationUpdate,
    user: RequireUserDependency,
    db: DatabaseDependency,
) -> ResponseModel[schemas.FitnessPlanParticipation]:
    participation = await get_or_fail(
        models.UserFitnessPlanParticipation, participation_id, db
    )

    if participation.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    if body.is_active is not None:
        if not participation.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You can't resume a fitness plan after leaving.",
            )
        participation.is_active = False
        await leave_fitness_plan(participation_id=participation.id, db=db)

    await db.commit()

    return ResponseModel(data=schemas.FitnessPlanParticipation.from_orm(participation))
