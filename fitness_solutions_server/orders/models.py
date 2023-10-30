from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from fitness_solutions_server.core.models import Base, TimestampMixin

if TYPE_CHECKING:
    from fitness_solutions_server.fitness_coaches.models import FitnessCoach
    from fitness_solutions_server.fitness_plans.models import FitnessPlan
    from fitness_solutions_server.workouts.models import Workout


class OrderType(str, Enum):
    workout = "workout"
    fitness_plan = "fitness_plan"


class OrderStatus(str, Enum):
    in_progress = "in_progress"
    pending_approval = "pending_approval"
    approved = "approved"
    declined = "declined"


class Order(Base, TimestampMixin):
    __tablename__ = "orders"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    type: Mapped[OrderType]
    description: Mapped[str]
    fitness_coach_id: Mapped[UUID] = mapped_column(
        ForeignKey("fitness_coaches.id", ondelete="CASCADE")
    )
    amount: Mapped[int]
    status: Mapped[OrderStatus] = mapped_column(default=OrderStatus.in_progress)
    decline_reason: Mapped[str | None]

    fitness_coach: Mapped[FitnessCoach] = relationship(
        back_populates="orders", passive_deletes=True
    )
    workouts: Mapped[list["Workout"]] = relationship(
        back_populates="order", passive_deletes=True
    )
    fitness_plans: Mapped[list["FitnessPlan"]] = relationship(
        back_populates="order", passive_deletes=True, cascade="all, delete"
    )
