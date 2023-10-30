from datetime import datetime
from typing import Annotated
from uuid import uuid4

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fitness_solutions_server.core.config import settings
from fitness_solutions_server.core.database import DatabaseDependency
from fitness_solutions_server.core.security import (
    create_security_token,
    generate_authentication_token,
    hash_password,
)
from fitness_solutions_server.fitness_coaches import models
from fitness_solutions_server.fitness_coaches.utils import (
    send_fitness_coach_activation_email,
)
from fitness_solutions_server.images.models import Image
from fitness_solutions_server.storage.base import (
    StorageService,
    StorageServiceDependency,
)


class FitnessCoachService:
    def __init__(self, db: AsyncSession, storage_service: StorageService):
        self.db = db
        self.storage_service = storage_service

    async def get_by_email(self, email: str) -> models.FitnessCoach | None:
        return await self.db.scalar(
            select(models.FitnessCoach).where(models.FitnessCoach.email == email)
        )

    async def get_by_activation_token(self, token: str) -> models.FitnessCoach | None:
        return await self.db.scalar(
            select(models.FitnessCoach).where(
                models.FitnessCoach.activation_token == token
            )
        )

    async def create(
        self, fitness_coach: models.FitnessCoach, profile_image: Image
    ) -> models.FitnessCoach:
        (raw_activation_code, hashed_activation_code) = create_security_token()
        fitness_coach.id = uuid4()
        profile_image_path = (
            f"fitness-coaches/{fitness_coach.id}/{profile_image.file_name}"
        )
        fitness_coach.activation_token = hashed_activation_code
        fitness_coach.password_hash = hash_password(str(uuid4()))
        fitness_coach.profile_image_path = profile_image_path
        self.db.add(fitness_coach)

        # Move profile image
        await self.storage_service.move(
            from_path=profile_image.path,
            to_path=profile_image_path,
        )
        await self.db.delete(profile_image)

        await self.db.commit()

        # TODO: Send on background task so we don't fail the request.
        await send_fitness_coach_activation_email(
            email=fitness_coach.email, token=raw_activation_code
        )

        return fitness_coach

    async def prepare_for_image_update(
        self, fitness_coach: models.FitnessCoach, image: Image
    ):
        profile_image_path = f"fitness-coaches/{fitness_coach.id}/{image.file_name}"
        fitness_coach.profile_image_path = profile_image_path
        await self.storage_service.move(
            from_path=image.path,
            to_path=profile_image_path,
        )
        await self.db.delete(image)

    async def activate(self, password: str, fitness_coach: models.FitnessCoach):
        fitness_coach.password_hash = hash_password(password)
        fitness_coach.activated_at = datetime.utcnow()
        fitness_coach.activation_token = None
        await self.db.commit()

    async def create_auth_token(self, fitness_coach: models.FitnessCoach) -> str:
        (unhashed_token, hashed_token) = generate_authentication_token()
        auth_token_model = models.FitnessCoachAuthenticationToken(
            token=hashed_token,
            fitness_coach_id=fitness_coach.id,
            expires_at=datetime.now().astimezone()
            + settings.FITNESS_COACH_AUTH_EXPIRE_DELTA,
        )
        self.db.add(auth_token_model)
        await self.db.commit()
        return unhashed_token


def get_fitness_coach_service(
    db: DatabaseDependency, storage_service: StorageServiceDependency
) -> FitnessCoachService:
    return FitnessCoachService(db=db, storage_service=storage_service)


FitnessCoachServiceDependency = Annotated[
    FitnessCoachService, Depends(get_fitness_coach_service)
]
