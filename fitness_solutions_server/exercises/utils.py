from typing import Tuple, cast
from uuid import UUID

from fitness_solutions_server.equipment.utils import equipment_models_to_schema
from fitness_solutions_server.images.models import Image
from fitness_solutions_server.muscle_groups.utils import muscle_group_models_to_schema
from fitness_solutions_server.pr_observations.models import PRObservation
from fitness_solutions_server.pr_observations.utils import (
    pr_observation_model_to_schema,
)
from fitness_solutions_server.storage.base import StorageService

from . import models, schemas


def exercise_model_to_schema(
    is_admin: bool,
    exercise: models.Exercise | Tuple[models.Exercise, PRObservation],
    storage_service: StorageService,
) -> schemas.Exercise | schemas.ExerciseAdmin:
    if isinstance(exercise, models.Exercise):
        _exercise = exercise
        latest_personal_record = None
    else:
        _exercise = exercise[0]
        latest_personal_record = exercise[1]

    muscle_groups = muscle_group_models_to_schema(
        _exercise.muscle_groups, is_admin=is_admin, storage_service=storage_service
    )
    equipment = equipment_models_to_schema(
        _exercise.equipment, is_admin=is_admin, storage_service=storage_service
    )

    if not is_admin:
        return schemas.Exercise(
            id=_exercise.id,
            name=_exercise.name,
            en_name=exercise.en_name,
            is_bodyweight=exercise.is_bodyweight,
            relative_bodyweight_intensity=exercise.relative_bodyweight_intensity,
            image_url=storage_service.link(path=_exercise.image_path),
            model_3d_url=storage_service.link(path=_exercise.model_3d_path),
            muscle_groups=muscle_groups,
            equipment=equipment,
            created_at=_exercise.created_at,
            updated_at=_exercise.updated_at,
            latest_personal_record=pr_observation_model_to_schema(
                latest_personal_record,
                is_admin=is_admin,
                storage_service=storage_service,
            )
            if latest_personal_record is not None
            else None,
        )
    else:
        return schemas.ExerciseAdmin(
            id=_exercise.id,
            name=_exercise.name,
            en_name=exercise.en_name,
            is_bodyweight=exercise.is_bodyweight,
            relative_bodyweight_intensity=exercise.relative_bodyweight_intensity,
            name_translations=_exercise.name_translations,
            image_url=storage_service.link(path=_exercise.image_path),
            model_3d_url=storage_service.link(path=_exercise.model_3d_path),
            muscle_groups=muscle_groups,
            equipment=equipment,
            created_at=_exercise.created_at,
            updated_at=_exercise.updated_at,
        )


def exercises_models_to_schema(
    exercises: list[models.Exercise] | list[Tuple[models.Exercise, PRObservation]],
    is_admin: bool,
    storage_service: StorageService,
) -> list[schemas.Exercise] | list[schemas.ExerciseAdmin]:
    # Weird why this cast is needed to satisfy the type checker...
    return cast(
        list[schemas.Exercise] | list[schemas.ExerciseAdmin],
        [
            exercise_model_to_schema(
                is_admin=is_admin, exercise=e, storage_service=storage_service
            )
            for e in exercises
        ],
    )


def make_exercises_image_path(id: UUID, image: Image) -> str:
    return f"exercises/{id}{image.file_extension}"
