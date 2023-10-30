from uuid import UUID

from sqlalchemy import literal, select
from sqlalchemy.exc import InvalidRequestError
from sqlalchemy.orm import selectinload
from sqlalchemy.orm.interfaces import ORMOption

from fitness_solutions_server.exercises.utils import exercise_model_to_schema
from fitness_solutions_server.fitness_coaches.mapper import FitnessCoachMapper
from fitness_solutions_server.saved_workouts.models import user_saved_workouts
from fitness_solutions_server.storage.base import StorageService

from . import models, schemas


def workout_model_to_schema(
    is_admin: bool,
    is_fitness_coach: bool,
    workout: models.Workout,
    storage_service: StorageService,
    fitness_coach_mapper: FitnessCoachMapper,
) -> schemas.WorkoutPrivate | schemas.Workout:
    workout_schema = schemas.Workout(
        id=workout.id,
        name=workout.name,
        description=workout.description,
        experience_level=workout.experience_level,
        user_id=workout.user_id,
        fitness_coach_id=workout.fitness_coach_id,
        created_at=workout.created_at,
        updated_at=workout.updated_at,
        focus=workout.focus,
        target_sex=workout.target_sex,
        is_saved=workout.is_saved,
        min_age=workout.min_age,
        max_age=workout.max_age,
    )

    if is_admin or is_fitness_coach:
        workout_schema = schemas.WorkoutPrivate(
            **workout_schema.dict(),
            order_id=workout.order_id,
            is_released=workout.is_released,
            name_translations=workout.name_translations,
            description_translations=workout.description_translations
        )

    try:
        workout_schema.exercises = [
            schemas.WorkoutExercise(
                id=we.id,
                exercise=exercise_model_to_schema(
                    is_admin=is_admin,
                    exercise=we.exercise,
                    storage_service=storage_service,
                ),
                order=we.order,
                sets=[schemas.WorkoutExerciseSet.from_orm(s) for s in we.sets],
            )
            for we in workout.workout_exercises
        ]
    except InvalidRequestError:
        pass

    if workout.fitness_coach is not None:
        workout_schema.fitness_coach = fitness_coach_mapper.fitness_coach_to_schema(
            workout.fitness_coach
        )

    return workout_schema


def workout_models_to_schema(
    workouts: list[models.Workout],
    is_admin: bool,
    is_fitness_coach: bool,
    storage_service: StorageService,
    fitness_coach_mapper: FitnessCoachMapper,
) -> list[schemas.WorkoutPrivate] | list[schemas.Workout]:
    return [
        workout_model_to_schema(
            is_admin=is_admin,
            is_fitness_coach=is_fitness_coach,
            workout=w,
            storage_service=storage_service,
            fitness_coach_mapper=fitness_coach_mapper,
        )
        for w in workouts
    ]


def options_for_embeds(
    embeds: set[schemas.WorkoutEmbedOption] | None,
) -> list[ORMOption]:
    options: list[ORMOption] = []

    if embeds is not None:
        if schemas.WorkoutEmbedOption.exercises in embeds:
            options.append(
                selectinload(models.Workout.workout_exercises).selectinload(
                    models.WorkoutExercise.exercise
                )
            )
            options.append(
                selectinload(models.Workout.workout_exercises).selectinload(
                    models.WorkoutExercise.sets
                )
            )
        if schemas.WorkoutEmbedOption.fitness_coach in embeds:
            options.append(selectinload(models.Workout.fitness_coach))

    return options


def is_saved_expression(user_id: UUID):
    return (
        select(literal(1, literal_execute=True))
        .select_from(user_saved_workouts)
        .where(user_saved_workouts.c.user_id == user_id)
        .where(user_saved_workouts.c.workout_id == models.Workout.id)
        .exists()
    )
