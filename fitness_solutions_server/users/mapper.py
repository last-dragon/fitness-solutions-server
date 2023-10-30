from typing import Annotated, Sequence

from fastapi import Depends

from fitness_solutions_server.storage.base import StorageServiceDependency
from fitness_solutions_server.core.utils import get_or_fail
from fitness_solutions_server.countries import models as country_models
from fitness_solutions_server.core.database import DatabaseDependency

from . import models, schemas


class UserMapper:
    def __init__(self, storage_service: StorageServiceDependency):
        self.storage_service = storage_service

    def user_to_schema(
        self,
        user: models.User,
    ) -> schemas.User:
        if user.profile_image_path is not None:
            profile_image_url = self.storage_service.link(user.profile_image_path)
        else:
            profile_image_url = user.profile_image_path
        return schemas.User(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            sex=user.sex,
            profile_image_url=profile_image_url,
            created_at=user.created_at,
            updated_at=user.updated_at,
            country=user.country,
        )

    def users_to_schema(self, users: Sequence[models.User]) -> list[schemas.User]:
        return [self.user_to_schema(fc) for fc in users]


UserMapperependency = Annotated[UserMapper, Depends()]
