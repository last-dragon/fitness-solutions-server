from typing import TYPE_CHECKING

from fitness_solutions_server.storage.base import StorageService

from . import models, schemas


def pr_observation_model_to_schema(
    pr_observation: models.PRObservation,
    is_admin: bool,
    storage_service: StorageService,
) -> schemas.PRObservation:
    from fitness_solutions_server.exercises.utils import exercise_model_to_schema

    return schemas.PRObservation(
        id=pr_observation.id,
        exercise_id=pr_observation.exercise_id,
        user_id=pr_observation.user_id,
        weight=pr_observation.weight,
        created_at=pr_observation.created_at,
        updated_at=pr_observation.updated_at,
        exercise=exercise_model_to_schema(
            is_admin=is_admin,
            exercise=pr_observation.exercise,
            storage_service=storage_service,
        )
        if pr_observation.exercise is not None
        else None,
    )


def pr_observation_models_to_schema(
    pr_observations: list[models.PRObservation],
    is_admin: bool,
    storage_service: StorageService,
) -> list[schemas.PRObservation]:
    return [
        pr_observation_model_to_schema(
            pr_observation=pr, is_admin=is_admin, storage_service=storage_service
        )
        for pr in pr_observations
    ]
