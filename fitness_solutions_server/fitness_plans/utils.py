from datetime import date, datetime, time
from typing import cast
from uuid import UUID

from sqlalchemy import delete, literal, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from fitness_solutions_server.equipment.models import Equipment
from fitness_solutions_server.equipment.utils import equipment_models_to_schema
from fitness_solutions_server.fitness_coaches.mapper import FitnessCoachMapper
from fitness_solutions_server.muscle_groups.schemas import MuscleGroup
from fitness_solutions_server.muscle_groups.utils import muscle_group_models_to_schema
from fitness_solutions_server.saved_fitness_plans.models import user_saved_fitness_plans
from fitness_solutions_server.storage.base import StorageService
from fitness_solutions_server.user_workouts.models import UserWorkout

from . import models, schemas


async def leave_fitness_plan(participation_id: UUID, db: AsyncSession):
    """
    Deletes all future planned workouts
    """
    await db.execute(
        delete(UserWorkout)
        .where(UserWorkout.fitness_plan_participation_id == participation_id)
        .where(UserWorkout.started_at >= datetime.combine(datetime.utcnow(), time.min))
    )
    await db.execute(
        update(models.UserFitnessPlanParticipation)
        .where(models.UserFitnessPlanParticipation.id == participation_id)
        .values(is_active=False)
    )


def workout_to_week_status(workout: UserWorkout) -> schemas.WeekStatus:
    if workout.completed_at is not None:
        return schemas.WeekStatus.done
    elif workout.started_at.date() < date.today():
        return schemas.WeekStatus.missed
    else:
        return schemas.WeekStatus.pending


def fitness_plan_model_to_schema(
    is_admin: bool,
    auth_fitness_coach_id: UUID | None,
    fitness_plan: models.FitnessPlan,
    fitness_coach_mapper: FitnessCoachMapper,
    storage_service: StorageService,
) -> schemas.FitnessPlanPrivate | schemas.FitnessPlanPublic:
    schema: schemas.FitnessPlanPrivate | schemas.FitnessPlanPublic = (
        schemas.FitnessPlanPublic(
            id=fitness_plan.id,
            name=fitness_plan.name,
            description=fitness_plan.description,
            experience_level=fitness_plan.experience_level,
            fitness_coach_id=fitness_plan.fitness_coach_id,
            created_at=fitness_plan.created_at,
            updated_at=fitness_plan.updated_at,
            focus=fitness_plan.focus,
            target_sex=fitness_plan.target_sex,
            min_age=fitness_plan.min_age,
            max_age=fitness_plan.max_age,
            number_of_workouts_per_week=fitness_plan.number_of_workouts_per_week,
            is_saved=fitness_plan.is_saved,
            is_released=fitness_plan.is_released,
        )
    )

    if is_admin or auth_fitness_coach_id == fitness_plan.fitness_coach_id:
        schema = schemas.FitnessPlanPrivate(
            **schema.dict(),
            order_id=fitness_plan.order_id,
            name_translations=fitness_plan.name_translations,
            description_translations=fitness_plan.description_translations
        )

    if fitness_plan.muscle_groups is not None:
        schema.muscle_groups = cast(
            list[MuscleGroup],
            muscle_group_models_to_schema(
                fitness_plan.muscle_groups,
                is_admin=False,
                storage_service=storage_service,
            ),
        )

    if fitness_plan.equipment is not None:
        schema.equipment = cast(
            list[Equipment],
            equipment_models_to_schema(
                fitness_plan.equipment,
                is_admin=False,
                storage_service=storage_service,
            ),
        )

    if fitness_plan.fitness_coach is not None:
        schema.fitness_coach = fitness_coach_mapper.fitness_coach_to_schema(
            fitness_plan.fitness_coach
        )

    return schema


def fitness_plan_models_to_schema(
    fitness_plans: list[models.FitnessPlan],
    is_admin: bool,
    auth_fitness_coach_id: UUID | None,
    fitness_coach_mapper: FitnessCoachMapper,
    storage_service: StorageService,
) -> list[schemas.FitnessPlanPrivate] | list[schemas.FitnessPlanPublic]:
    return cast(
        list[schemas.FitnessPlanPrivate] | list[schemas.FitnessPlanPublic],
        [
            fitness_plan_model_to_schema(
                is_admin=is_admin,
                auth_fitness_coach_id=auth_fitness_coach_id,
                fitness_plan=fp,
                fitness_coach_mapper=fitness_coach_mapper,
                storage_service=storage_service,
            )
            for fp in fitness_plans
        ],
    )


def is_saved_expression(user_id: UUID):
    return (
        select(literal(1, literal_execute=True))
        .select_from(user_saved_fitness_plans)
        .where(user_saved_fitness_plans.c.user_id == user_id)
        .where(user_saved_fitness_plans.c.fitness_plan_id == models.FitnessPlan.id)
        .exists()
    )
