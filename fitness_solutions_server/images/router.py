import mimetypes
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, Header, HTTPException, UploadFile, status

from fitness_solutions_server.admins.dependencies import (
    require_admin_authentication_token,
)
from fitness_solutions_server.core.database import DatabaseDependency
from fitness_solutions_server.core.schemas import ResponseModel
from fitness_solutions_server.storage.base import StorageServiceDependency

from . import models, schemas

router = APIRouter(prefix="/images")

MAX_FILE_SIZE = 2097152  # 2mb


@router.post("", dependencies=[Depends(require_admin_authentication_token)])
async def upload_image(
    file: UploadFile,
    content_length: Annotated[int, Header(lt=MAX_FILE_SIZE)],
    storage_service: StorageServiceDependency,
    db: DatabaseDependency,
) -> ResponseModel[schemas.Image]:
    # Verify file type
    if file.content_type not in ["image/png", "image/jpeg"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only png or jpeg images are allowed.",
        )

    # TODO: Maybe use middleware instead (https://github.com/tiangolo/fastapi/blob/8cc967a7605d3883bd04ceb5d25cc94ae079612f/tests/test_custom_middleware_exception.py#L4)
    # and pass the file object directly to the service (so that S3 can use upload_fileobj).
    # let's not worry too much about this file stuff unless it becomes a problem...

    # Verify file size
    file_bytes = bytes()
    while chunk := await file.read(1024):
        file_bytes += chunk
        if len(file_bytes) > content_length:
            raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)

    # Upload image to storage
    image_id = uuid4()
    image = models.Image(id=image_id)
    file_extension = mimetypes.guess_extension(file.content_type)
    path = f"uploads/{image.id}{file_extension}"
    await storage_service.upload(bytes=file_bytes, path=path)

    # Save to database
    image.path = path
    db.add(image)
    await db.commit()

    return ResponseModel(data=schemas.Image(id=image_id))
