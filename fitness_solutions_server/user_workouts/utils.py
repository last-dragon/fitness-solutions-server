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
from fitness_solutions_server.storage.base import (
    StorageService,
)


class UserWorkoutService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_workouts_by_workouts_id(
        self, workouts_id: UUID
    ) -> models.UserWorkout | None:
        return await self.db.scalar(
            select(models.UserWorkout).where(
                models.UserWorkout.workout_id == workouts_id
            )
        )


def get_user_service(db: DatabaseDependency) -> UserWorkoutService:
    return UserWorkoutService(db=db)


UserWorkoutServiceDependency = Annotated[UserWorkoutService, Depends(get_user_service)]
