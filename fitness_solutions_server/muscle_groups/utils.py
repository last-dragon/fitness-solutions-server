from typing import Sequence
from uuid import UUID

from fitness_solutions_server.images.models import Image
from fitness_solutions_server.storage.base import StorageService

from . import models, schemas


def muscle_group_model_to_schema(
    is_admin: bool, muscle_group: models.MuscleGroup, storage_service: StorageService
) -> schemas.MuscleGroupAdmin | schemas.MuscleGroup:
    if not is_admin:
        return schemas.MuscleGroup(
            id=muscle_group.id,
            name=muscle_group.name,
            image_url=storage_service.link(path=muscle_group.image_path),
            body_part=muscle_group.body_part,
            created_at=muscle_group.created_at,
            updated_at=muscle_group.updated_at,
        )
    else:
        return schemas.MuscleGroupAdmin(
            id=muscle_group.id,
            name=muscle_group.name,
            name_translations=muscle_group.name_translations,
            image_url=storage_service.link(path=muscle_group.image_path),
            body_part=muscle_group.body_part,
            created_at=muscle_group.created_at,
            updated_at=muscle_group.updated_at,
        )


def muscle_group_models_to_schema(
    muscle_groups: Sequence[models.MuscleGroup],
    is_admin: bool,
    storage_service: StorageService,
) -> list[schemas.MuscleGroupAdmin] | list[schemas.MuscleGroup]:
    return [
        muscle_group_model_to_schema(
            is_admin=is_admin, muscle_group=e, storage_service=storage_service
        )
        for e in muscle_groups
    ]


def make_muscle_group_image_path(id: UUID, image: Image) -> str:
    return f"muscle-groups/{id}{image.file_extension}"
