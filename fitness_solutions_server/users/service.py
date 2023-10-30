from datetime import datetime

from typing import Annotated
from uuid import UUID

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fitness_solutions_server.core.config import settings
from fitness_solutions_server.core.database import DatabaseDependency
from fitness_solutions_server.core.security import generate_authentication_token

from . import models
from fitness_solutions_server.images import models as imodels
from fitness_solutions_server.storage.base import (
    StorageService,
    StorageServiceDependency,
)

# import itsdangerous


class UserService:
    def __init__(self, db: AsyncSession, storage_service: StorageService):
        self.db = db
        self.storage_service = storage_service

    async def get_by_email(self, email: str) -> models.User | None:
        return await self.db.scalar(
            select(models.User).where(models.User.email == email)
        )

    async def get_profile_image_url_by_id(
        self, profile_image_id: UUID
    ) -> imodels.Image | None:
        return await self.db.scalar(
            select(imodels.Image.path).where(imodels.Image.id == profile_image_id)
        )

    async def create(
        self, user: models.User, profile_image: imodels.Image
    ) -> models.User:
        profile_image_path = f"users/{user.id}/{profile_image.file_name}"
        user.profile_image_path = profile_image_path
        self.db.add(user)

        # Move to Image
        await self.storage_service.move(
            from_path=profile_image.path,
            to_path=profile_image_path,
        )
        await self.db.delete(profile_image)

        await self.db.commit()

    async def prepare_for_image_update(self, user: models.User, image: imodels.Image):
        profile_image_path = f"users/{user.id}/{image.file_name}"
        user.profile_image_path = profile_image_path

        await self.storage_service.move(
            from_path=image.path,
            to_path=profile_image_path,
        )
        await self.db.delete(image)

    async def get_by_verification_code(self, code: str) -> models.User | None:
        return await self.db.scalar(
            select(models.User).where(models.User.verification_code == code)
        )

    async def mark_verified(self, user: models.User):
        user.verification_code = None
        user.verified_at = datetime.utcnow()
        await self.db.commit()

    async def create_auth_token(self, user: models.User) -> str:
        (unhashed_token, hashed_token) = generate_authentication_token()
        auth_token_model = models.UserAuthenticationToken(
            token=hashed_token,
            user_id=user.id,
            expires_at=datetime.now().astimezone() + settings.USER_AUTH_EXPIRE_DELTA,
        )
        self.db.add(auth_token_model)
        await self.db.commit()
        return unhashed_token


def get_user_service(
    db: DatabaseDependency, storage_service: StorageServiceDependency
) -> UserService:
    return UserService(db=db, storage_service=storage_service)


UserServiceDependency = Annotated[UserService, Depends(get_user_service)]
