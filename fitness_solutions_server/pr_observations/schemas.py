from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field

from fitness_solutions_server.core.schemas import TimestampMixin
from fitness_solutions_server.exercises.schemas import Exercise


class PRObservationEmbed(str, Enum):
    exercise = "exercise"


class PRObservationCreate(BaseModel):
    exercise_id: UUID
    weight: float = Field(description="Weight in kg", ge=0)


class PRObservation(TimestampMixin, BaseModel):
    id: UUID
    exercise_id: UUID
    user_id: UUID
    weight: float
    exercise: Exercise | None

    class Config:
        orm_mode = True
