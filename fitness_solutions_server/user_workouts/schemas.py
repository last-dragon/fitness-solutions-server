from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from fitness_solutions_server.core.models import TimestampMixin
from fitness_solutions_server.workouts.schemas import Workout


class UserWorkoutCreate(BaseModel):
    workout_id: UUID


class UserWorkout(TimestampMixin, BaseModel):
    id: UUID
    workout_id: UUID
    user_id: UUID
    fitness_plan_participation_id: UUID | None
    completed_at: datetime | None
    started_at: datetime
    workout: Workout | None

    class Config:
        orm_mode = True
