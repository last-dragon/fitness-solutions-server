from datetime import date, datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, ForeignKey, select
from sqlalchemy.dialects.postgresql import CITEXT
from sqlalchemy.orm import Mapped, column_property, mapped_column, relationship

from fitness_solutions_server.core.models import Base, Focus, Sex, TimestampMixin
from fitness_solutions_server.countries.models import Country
from fitness_solutions_server.pr_observations.models import PRObservation
from fitness_solutions_server.saved_workouts.models import user_saved_workouts
from fitness_solutions_server.user_workouts.models import UserWorkout
from fitness_solutions_server.weight_logs.models import WeightLog

if TYPE_CHECKING:
    from fitness_solutions_server.workouts.models import Workout


class User(TimestampMixin, Base):
    __tablename__ = "users"
    __table_args__ = (CheckConstraint("height > 0", name="height_constraint"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    email: Mapped[str] = mapped_column(CITEXT(), unique=True)
    password_hash: Mapped[str]
    full_name: Mapped[str]
    sex: Mapped[Sex | None]
    height: Mapped[float | None]
    weight: Mapped[float | None] = column_property(
        select(WeightLog.weight)
        .where(WeightLog.user_id == id)
        .order_by(WeightLog.created_at.desc())
        .limit(1)
        .correlate_except(WeightLog)
        .scalar_subquery()
    )
    birthdate: Mapped[date | None]
    focus: Mapped[Focus | None]
    verification_code: Mapped[str | None] = mapped_column(unique=True)
    verified_at: Mapped[datetime | None]
    country_id: Mapped[UUID] = mapped_column(ForeignKey("countries.id"))

    profile_image_path: Mapped[str]

    authentication_tokens: Mapped[list["UserAuthenticationToken"]] = relationship(
        back_populates="user", passive_deletes=True
    )
    country: Mapped[Country] = relationship(
        back_populates="users", lazy="joined", passive_deletes=True
    )
    workouts: Mapped[list["Workout"]] = relationship(
        back_populates="user", lazy="noload", passive_deletes=True
    )
    saved_workouts: Mapped[list["Workout"]] = relationship(
        secondary=user_saved_workouts, lazy="noload", passive_deletes=True
    )
    tracked_workouts: Mapped[list["UserWorkout"]] = relationship(
        back_populates="user", lazy="noload", passive_deletes=True
    )
    weight_logs: Mapped[list["WeightLog"]] = relationship(
        back_populates="user",
        lazy="noload",
        passive_deletes=True,
        cascade="all, delete",
    )
    pr_observations: Mapped[list[PRObservation]] = relationship(
        back_populates="user",
        passive_deletes=True,
        cascade="all, delete",
        lazy="noload",
    )


class UserAuthenticationToken(TimestampMixin, Base):
    __tablename__ = "user_authentication_tokens"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    token: Mapped[str] = mapped_column(unique=True)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    expires_at: Mapped[datetime]

    user: Mapped[User] = relationship(back_populates="authentication_tokens")
