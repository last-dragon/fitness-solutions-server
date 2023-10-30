from uuid import UUID

from fitness_solutions_server.images.models import Image
from fitness_solutions_server.storage.base import StorageService

from . import models, schemas


def equipment_model_to_schema(
    is_admin: bool, equipment: models.Equipment, storage_service: StorageService
) -> schemas.Equipment | schemas.EquipmentAdmin:
    if not is_admin:
        return schemas.Equipment(
            id=equipment.id,
            name=equipment.name,
            image_url=storage_service.link(path=equipment.image_path),
            created_at=equipment.created_at,
            updated_at=equipment.updated_at,
            consecutive_terms=equipment.consecutive_terms,
        )
    else:
        return schemas.EquipmentAdmin(
            id=equipment.id,
            name=equipment.name,
            name_translations=equipment.name_translations,
            image_url=storage_service.link(path=equipment.image_path),
            created_at=equipment.created_at,
            updated_at=equipment.updated_at,
            consecutive_terms=equipment.consecutive_terms,
        )


def equipment_models_to_schema(
    equipment: list[models.Equipment], is_admin: bool, storage_service: StorageService
) -> list[schemas.Equipment] | list[schemas.EquipmentAdmin]:
    return [
        equipment_model_to_schema(
            is_admin=is_admin, equipment=e, storage_service=storage_service
        )
        for e in equipment
    ]


def make_equipment_image_path(id: UUID, image: Image) -> str:
    return f"equipment/{id}{image.file_extension}"
