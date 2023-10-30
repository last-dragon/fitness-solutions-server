from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from fitness_solutions_server.core.models import Base, TimestampMixin

if TYPE_CHECKING:
    from fitness_solutions_server.exercises.models import Exercise
    from fitness_solutions_server.users.models import User


class PRObservation(TimestampMixin, Base):
    __tablename__ = "pr_observations"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    exercise_id: Mapped[UUID] = mapped_column(
        ForeignKey("exercises.id", ondelete="CASCADE")
    )
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    weight: Mapped[float]

    exercise: Mapped[Exercise | None] = relationship(
        back_populates="pr_observations", lazy="noload"
    )
    user: Mapped[User | None] = relationship(
        back_populates="pr_observations", lazy="noload"
    )

    __table_args__ = (Index(None, user_id, exercise_id),)
