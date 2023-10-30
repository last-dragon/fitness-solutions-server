from uuid import UUID

from pydantic import BaseModel, Field

from fitness_solutions_server.core.schemas import TimestampMixin
from fitness_solutions_server.orders.models import OrderStatus, OrderType


class OrderCreate(BaseModel):
    description: str
    fitness_coach_id: UUID
    type: OrderType
    amount: int = Field(
        description="The amount that the coach must supply, for example 2 exercises.",
        ge=1,
    )


class OrderDeclineBody(BaseModel):
    reason: str


class OrderUpdate(BaseModel):
    description: str | None


class Order(TimestampMixin, BaseModel):
    id: UUID
    description: str
    fitness_coach_id: UUID
    type: OrderType
    amount: int
    status: OrderStatus
    decline_reason: str | None

    class Config:
        orm_mode = True
