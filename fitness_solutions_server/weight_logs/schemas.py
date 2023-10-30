from uuid import UUID

from pydantic import BaseModel, Field

from fitness_solutions_server.core.schemas import TimestampMixin


class WeightLogCreate(BaseModel):
    weight: float = Field(description="Weight in kg")


class WeightLog(TimestampMixin, BaseModel):
    id: UUID
    weight: float = Field(description="Weight in kg")
    user_id: UUID

    class Config:
        orm_mode = True
