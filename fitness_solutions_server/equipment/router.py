import functools
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, status
from fastapi_pagination import pagination_ctx
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy import select

from fitness_solutions_server.admins.dependencies import (
    IsAdminDependency,
    require_admin_authentication_token,
)
from fitness_solutions_server.core.database import DatabaseDependency
from fitness_solutions_server.core.schemas import ResponseModel
from fitness_solutions_server.core.utils import CursorPage, get_or_fail
from fitness_solutions_server.equipment.utils import (
    equipment_model_to_schema,
    equipment_models_to_schema,
    make_equipment_image_path,
)
from fitness_solutions_server.images.models import Image
from fitness_solutions_server.storage.base import StorageServiceDependency

from . import models, schemas

router = APIRouter(prefix="/equipment")


@router.post(
    "",
    dependencies=[Depends(require_admin_authentication_token)],
    status_code=status.HTTP_201_CREATED,
)
async def create_equipment(
    create_equipment_request: schemas.EquipmentCreate,
    db: DatabaseDependency,
    storage_service: StorageServiceDependency,
) -> ResponseModel[schemas.EquipmentAdmin]:
    # Load image
    # TODO: Maybe we need FOR UPDATE here, since we move it.
    image = await get_or_fail(Image, create_equipment_request.image_id, db)

    equipment_id = uuid4()
    equipment_image_path = f"equipment/{equipment_id}{image.file_extension}"
    equipment = models.Equipment(
        id=equipment_id,
        name_translations=create_equipment_request.name_translations,
        image_path=equipment_image_path,
        consecutive_terms=create_equipment_request.consecutive_terms,
    )
    db.add(equipment)
    await db.flush()

    # Move image
    await storage_service.move(from_path=image.path, to_path=equipment_image_path)
    await db.delete(image)

    await db.commit()

    return ResponseModel(
        data=equipment_model_to_schema(
            is_admin=True, equipment=equipment, storage_service=storage_service
        )
    )


@router.get("/{equipment_id}")
async def get_equipment(
    equipment_id: UUID,
    db: DatabaseDependency,
    storage_service: StorageServiceDependency,
    is_admin: IsAdminDependency,
) -> ResponseModel[schemas.EquipmentAdmin | schemas.Equipment]:
    equipment = await get_or_fail(models.Equipment, equipment_id, db)
    return ResponseModel(
        data=equipment_model_to_schema(
            is_admin=is_admin, equipment=equipment, storage_service=storage_service
        )
    )


@router.get("", dependencies=[Depends(pagination_ctx(CursorPage))])
async def list_equipment(
    db: DatabaseDependency,
    storage_service: StorageServiceDependency,
    is_admin: IsAdminDependency,
) -> ResponseModel[CursorPage[schemas.EquipmentAdmin] | CursorPage[schemas.Equipment]]:
    equipment = await paginate(
        db,
        select(models.Equipment).order_by(models.Equipment.id),
        transformer=functools.partial(
            equipment_models_to_schema,
            is_admin=is_admin,
            storage_service=storage_service,
        ),
    )
    return ResponseModel(data=equipment)


@router.delete(
    "/{equipment_id}", dependencies=[Depends(require_admin_authentication_token)]
)
async def delete_equipment(
    equipment_id: UUID, db: DatabaseDependency
) -> ResponseModel[None]:
    equipment = await get_or_fail(models.Equipment, equipment_id, db)
    equipment.delete()
    await db.commit()

    return ResponseModel(data=None)


@router.patch(
    "/{equipment_id}", dependencies=[Depends(require_admin_authentication_token)]
)
async def update_equipment(
    equipment_id: UUID,
    equipment_update: schemas.EquipmentUpdate,
    db: DatabaseDependency,
    storage_service: StorageServiceDependency,
) -> ResponseModel[schemas.EquipmentAdmin]:
    equipment = await get_or_fail(models.Equipment, equipment_id, db)

    if equipment_update.name_translations is not None:
        equipment.name_translations = equipment_update.name_translations
    if equipment_update.consecutive_terms is not None:
        equipment.consective_terms = equipment_update.consecutive_terms
    if equipment_update.image_id is not None:
        image = await get_or_fail(Image, equipment_update.image_id, db)
        equipment.image_path = make_equipment_image_path(id=equipment_id, image=image)
        await storage_service.move(from_path=image.path, to_path=equipment.image_path)
        await db.delete(image)

    await db.commit()

    return ResponseModel(
        data=equipment_model_to_schema(
            is_admin=True, equipment=equipment, storage_service=storage_service
        )
    )
