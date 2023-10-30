from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, status
from sqlalchemy import select

from fitness_solutions_server.admins.dependencies import (
    IsAdminDependency,
    require_admin_authentication_token,
)
from fitness_solutions_server.core.database import DatabaseDependency
from fitness_solutions_server.core.schemas import ResponseModel
from fitness_solutions_server.core.utils import get_or_fail
from fitness_solutions_server.images.models import Image
from fitness_solutions_server.muscle_groups.utils import (
    make_muscle_group_image_path,
    muscle_group_model_to_schema,
    muscle_group_models_to_schema,
)
from fitness_solutions_server.storage.base import StorageServiceDependency

from . import models, schemas

router = APIRouter(prefix="/muscle-groups")


@router.post(
    "",
    dependencies=[Depends(require_admin_authentication_token)],
    status_code=status.HTTP_201_CREATED,
)
async def create_muscle_group(
    create_muscle_group_request: schemas.MuscleGroupCreate,
    db: DatabaseDependency,
    storage_service: StorageServiceDependency,
) -> ResponseModel[schemas.MuscleGroupAdmin]:
    # Load image
    # TODO: Maybe we need FOR UPDATE here, since we move it.
    image = await get_or_fail(Image, create_muscle_group_request.image_id, db)

    muscle_group_id = uuid4()
    muscle_group_image_path = make_muscle_group_image_path(
        id=muscle_group_id, image=image
    )
    muscle_group = models.MuscleGroup(
        id=muscle_group_id,
        name_translations=create_muscle_group_request.name_translations,
        image_path=muscle_group_image_path,
        body_part=create_muscle_group_request.body_part,
    )
    db.add(muscle_group)
    await db.flush()

    # Move image
    await storage_service.move(from_path=image.path, to_path=muscle_group_image_path)
    await db.delete(image)

    await db.commit()

    return ResponseModel(
        data=muscle_group_model_to_schema(
            is_admin=True, muscle_group=muscle_group, storage_service=storage_service
        )
    )


@router.get("/{muscle_group_id}")
async def get_muscle_group(
    muscle_group_id: UUID,
    db: DatabaseDependency,
    storage_service: StorageServiceDependency,
    is_admin: IsAdminDependency,
) -> ResponseModel[schemas.MuscleGroupAdmin | schemas.MuscleGroup]:
    muscle_group = await get_or_fail(models.MuscleGroup, muscle_group_id, db)
    return ResponseModel(
        data=muscle_group_model_to_schema(
            is_admin=is_admin,
            muscle_group=muscle_group,
            storage_service=storage_service,
        )
    )


@router.get("", summary="List muscle groups")
async def list_muscle_groups(
    db: DatabaseDependency,
    storage_service: StorageServiceDependency,
    is_admin: IsAdminDependency,
) -> ResponseModel[list[schemas.MuscleGroupAdmin] | list[schemas.MuscleGroup]]:
    muscle_groups_db = (await db.scalars(select(models.MuscleGroup))).all()
    muscle_groups = muscle_group_models_to_schema(
        muscle_groups=muscle_groups_db,
        is_admin=is_admin,
        storage_service=storage_service,
    )
    return ResponseModel(data=muscle_groups)


@router.delete(
    "/{muscle_group_id}", dependencies=[Depends(require_admin_authentication_token)]
)
async def delete_muscle_group(
    muscle_group_id: UUID, db: DatabaseDependency
) -> ResponseModel[None]:
    muscle_group = await get_or_fail(models.MuscleGroup, muscle_group_id, db)
    muscle_group.delete()
    await db.commit()

    return ResponseModel(data=None)


@router.patch(
    "/{muscle_group_id}", dependencies=[Depends(require_admin_authentication_token)]
)
async def update_muscle_group(
    muscle_group_id: UUID,
    muscle_group_update: schemas.MuscleGroupUpdate,
    db: DatabaseDependency,
    storage_service: StorageServiceDependency,
) -> ResponseModel[schemas.MuscleGroupAdmin]:
    muscle_group = await get_or_fail(models.MuscleGroup, muscle_group_id, db)

    if muscle_group_update.name_translations is not None:
        muscle_group.name_translations = muscle_group_update.name_translations

    if muscle_group_update.body_part is not None:
        muscle_group.body_part = muscle_group_update.body_part

    if muscle_group_update.image_id is not None:
        image = await get_or_fail(Image, muscle_group_update.image_id, db)
        muscle_group.image_path = make_muscle_group_image_path(
            id=muscle_group_id, image=image
        )
        await storage_service.move(
            from_path=image.path, to_path=muscle_group.image_path
        )
        await db.delete(image)

    await db.commit()

    return ResponseModel(
        data=muscle_group_model_to_schema(
            is_admin=True, muscle_group=muscle_group, storage_service=storage_service
        )
    )
