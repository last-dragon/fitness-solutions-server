import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from fitness_solutions_server.core.models import Base, TimestampMixin

if TYPE_CHECKING:
    from fitness_solutions_server.fitness_plans.models import (
        UserFitnessPlanParticipation,
    )
    from fitness_solutions_server.users.models import User
    from fitness_solutions_server.workouts.models import Workout


class UserWorkout(TimestampMixin, Base):
    __tablename__ = "user_workouts"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    workout_id: Mapped[UUID] = mapped_column(ForeignKey("workouts.id"))
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    fitness_plan_participation_id = mapped_column(
        ForeignKey("user_fitness_plans_participations.id", ondelete="CASCADE")
    )
    completed_at: Mapped[datetime.datetime | None]
    started_at: Mapped[datetime.datetime]

    workout: Mapped["Workout"] = relationship(
        lazy="noload", back_populates="user_workouts"
    )
    user: Mapped["User"] = relationship(
        lazy="noload", back_populates="tracked_workouts"
    )
    fitness_plan_participation: Mapped["UserFitnessPlanParticipation"] = relationship()
