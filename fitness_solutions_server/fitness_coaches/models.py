from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Column, ForeignKey, Table, false, func, select, true
from sqlalchemy.dialects.postgresql import CITEXT
from sqlalchemy.orm import Mapped, column_property, mapped_column, relationship

from fitness_solutions_server.core.models import Base, Sex, TimestampMixin
from fitness_solutions_server.countries.models import Country
from fitness_solutions_server.fitness_plans.models import FitnessPlan
from fitness_solutions_server.orders.models import Order
from fitness_solutions_server.workouts.models import Workout

fitness_coach_countries = Table(
    "fitness_coach_countries",
    Base.metadata,
    Column(
        "fitness_coach_id",
        ForeignKey("fitness_coaches.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "country_id", ForeignKey("countries.id", ondelete="CASCADE"), primary_key=True
    ),
)


class FitnessCoach(TimestampMixin, Base):
    __tablename__ = "fitness_coaches"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    full_name: Mapped[str]
    email: Mapped[str] = mapped_column(CITEXT(), unique=True)
    password_hash: Mapped[str]
    title: Mapped[str]
    description: Mapped[str]
    sex: Mapped[Sex]
    activation_token: Mapped[str | None] = mapped_column(unique=True)
    activated_at: Mapped[datetime | None]
    profile_image_path: Mapped[str]
    number_of_workouts: Mapped[int] = column_property(
        select(func.count(Workout.id))
        .where(Workout.fitness_coach_id == id)
        .where(Workout.is_released == true())
        .correlate_except(Workout)
        .scalar_subquery()
    )
    number_of_fitness_plans: Mapped[int] = column_property(
        select(func.count(FitnessPlan.id))
        .where(FitnessPlan.fitness_coach_id == id)
        .where(FitnessPlan.is_released == true())
        .correlate_except(FitnessPlan)
        .scalar_subquery()
    )
    is_released: Mapped[bool] = mapped_column(default=False, server_default=false())

    authentication_tokens: Mapped[
        list["FitnessCoachAuthenticationToken"]
    ] = relationship(back_populates="fitness_coach", passive_deletes=True)
    countries: Mapped[list[Country]] = relationship(
        secondary=fitness_coach_countries, passive_deletes=True
    )
    orders: Mapped[list["Order"]] = relationship(
        back_populates="fitness_coach",
        passive_deletes=True,
        cascade="all, delete",
    )
    workouts: Mapped[list["Workout"]] = relationship(
        back_populates="fitness_coach", passive_deletes=True, cascade="all, delete"
    )
    fitness_plans: Mapped[list["FitnessPlan"]] = relationship(
        back_populates="fitness_coach", passive_deletes=True, cascade="all, delete"
    )


class FitnessCoachAuthenticationToken(TimestampMixin, Base):
    __tablename__ = "fitness_coach_authentication_tokens"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    token: Mapped[str] = mapped_column(unique=True)
    fitness_coach_id: Mapped[UUID] = mapped_column(
        ForeignKey("fitness_coaches.id", ondelete="CASCADE"), index=True
    )
    expires_at: Mapped[datetime]

    fitness_coach: Mapped[FitnessCoach] = relationship(
        back_populates="authentication_tokens"
    )
