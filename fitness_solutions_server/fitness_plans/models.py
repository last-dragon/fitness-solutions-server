from __future__ import annotations

import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    UniqueConstraint,
    func,
    select,
    true,
    type_coerce,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import Mapped, mapped_column, query_expression, relationship

from fitness_solutions_server.core.localization import translation_hybrid
from fitness_solutions_server.core.models import (
    Base,
    ExperienceLevel,
    Focus,
    Sex,
    TimestampMixin,
)
from fitness_solutions_server.equipment.models import Equipment
from fitness_solutions_server.muscle_groups.models import MuscleGroup
from fitness_solutions_server.users.models import User

if TYPE_CHECKING:
    from fitness_solutions_server.fitness_coaches.models import FitnessCoach
    from fitness_solutions_server.orders.models import Order
    from fitness_solutions_server.workouts.models import Workout


class FitnessPlan(Base, TimestampMixin):
    __tablename__ = "fitness_plans"
    __table_args__ = (
        CheckConstraint(
            "min_age >= 0 AND min_age <= max_age",
            name="fitness_plan_age_constraints",
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name_translations: Mapped[dict[str, str]] = mapped_column(
        MutableDict.as_mutable(JSONB())
    )
    name = translation_hybrid(name_translations)
    description_translations: Mapped[dict[str, str]] = mapped_column(
        MutableDict.as_mutable(JSONB())
    )
    description = translation_hybrid(description_translations)
    experience_level: Mapped[ExperienceLevel]
    fitness_coach_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("fitness_coaches.id", ondelete="SET NULL"), index=True
    )
    order_id: Mapped[UUID] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"))
    is_released: Mapped[bool] = mapped_column(default=False)
    number_of_workouts_per_week: Mapped[int]
    focus: Mapped[Focus | None]
    target_sex: Mapped[Sex | None]
    min_age: Mapped[int | None]
    max_age: Mapped[int | None]
    is_saved: Mapped[bool | None] = query_expression()

    fitness_coach: Mapped[FitnessCoach | None] = relationship(
        back_populates="fitness_plans", lazy="noload"
    )
    order: Mapped[Order] = relationship(back_populates="fitness_plans", lazy="noload")
    weeks: Mapped[list["FitnessPlanWeek"]] = relationship(
        back_populates="fitness_plan",
        lazy="noload",
        passive_deletes=True,
        cascade="all, delete",
    )
    muscle_groups: Mapped[list[MuscleGroup] | None] = relationship(
        primaryjoin="FitnessPlanWeek.fitness_plan_id == FitnessPlan.id",
        secondary="join(FitnessPlanWeek, FitnessPlanWeekWorkout, FitnessPlanWeekWorkout.fitness_plan_week_id == FitnessPlanWeek.id)."
        "join(WorkoutExercise, WorkoutExercise.workout_id == FitnessPlanWeekWorkout.workout_id)."
        "join(exercise_muscle_groups, exercise_muscle_groups.c.exercise_id == WorkoutExercise.exercise_id)",
        viewonly=True,
        lazy="noload",
    )
    equipment: Mapped[list[Equipment] | None] = relationship(
        primaryjoin="FitnessPlanWeek.fitness_plan_id == FitnessPlan.id",
        secondary="join(FitnessPlanWeek, FitnessPlanWeekWorkout, FitnessPlanWeekWorkout.fitness_plan_week_id == FitnessPlanWeek.id)."
        "join(WorkoutExercise, WorkoutExercise.workout_id == FitnessPlanWeekWorkout.workout_id)."
        "join(exercise_equipment, exercise_equipment.c.exercise_id == WorkoutExercise.exercise_id)",
        viewonly=True,
        lazy="noload",
    )
    participations: Mapped[list["UserFitnessPlanParticipation"]] = relationship(
        lazy="noload"
    )

    @hybrid_property
    def participants_count(self) -> int:
        return len(self.participations)

    @participants_count.inplace.expression
    @classmethod
    def _participants_count_expression(cls):
        return type_coerce(
            select(func.count())
            .select_from(UserFitnessPlanParticipation)
            .where(UserFitnessPlanParticipation.fitness_plan_id == cls.id)
            .scalar_subquery(),
            Integer,
        )


class FitnessPlanWeek(Base, TimestampMixin):
    __tablename__ = "fitness_plan_weeks"
    __table_args__ = (
        UniqueConstraint(
            "fitness_plan_id",
            "order",
            name="fitness_plan_weeks_unique_order",
            deferrable=True,
            initially="DEFERRED",
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    fitness_plan_id: Mapped[UUID] = mapped_column(
        ForeignKey("fitness_plans.id", ondelete="CASCADE"), index=True
    )
    order: Mapped[int]

    fitness_plan: Mapped[FitnessPlan] = relationship(
        back_populates="weeks", lazy="noload"
    )
    workouts: Mapped[list[Workout]] = relationship(
        secondary="fitness_plan_week_workouts",
        lazy="noload",
        viewonly=True,
    )
    workout_associations: Mapped[list["FitnessPlanWeekWorkout"]] = relationship(
        back_populates="fitness_plan_week",
        lazy="noload",
        passive_deletes=True,
        cascade="all, delete",
    )


class FitnessPlanWeekWorkout(Base, TimestampMixin):
    __tablename__ = "fitness_plan_week_workouts"
    __table_args__ = (
        UniqueConstraint(
            "fitness_plan_week_id",
            "order",
            name="fitness_plan_week_workouts_unique_order",
            deferrable=True,
            initially="DEFERRED",
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    fitness_plan_week_id: Mapped[UUID] = mapped_column(
        ForeignKey("fitness_plan_weeks.id", ondelete="CASCADE"), index=True
    )
    workout_id: Mapped[UUID] = mapped_column(
        ForeignKey("workouts.id", ondelete="CASCADE")
    )
    order: Mapped[int]

    fitness_plan_week: Mapped[FitnessPlanWeek] = relationship(
        back_populates="workout_associations", lazy="noload"
    )
    workout: Mapped[Workout] = relationship(lazy="noload")


class UserFitnessPlanParticipation(TimestampMixin, Base):
    __tablename__ = "user_fitness_plans_participations"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    fitness_plan_id: Mapped[UUID] = mapped_column(
        ForeignKey("fitness_plans.id"), index=True
    )

    user: Mapped[User] = relationship()
    fitness_plan: Mapped[FitnessPlan] = relationship(back_populates="participations")
    is_active: Mapped[bool] = mapped_column(default=False)
    started_at: Mapped[datetime.date]

    __table_args__ = (
        Index(
            None,
            user_id,
            unique=True,
            postgresql_where=(is_active == true()),
        ),
    )
