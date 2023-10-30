from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Integer,
    UniqueConstraint,
    func,
    select,
    type_coerce,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.associationproxy import AssociationProxy, association_proxy
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import Mapped, mapped_column, query_expression, relationship

from fitness_solutions_server.core.localization import translation_hybrid
from fitness_solutions_server.core.models import (
    Base,
    ExperienceLevel,
    Focus,
    Sex,
    SoftDeleteMixin,
    TimestampMixin,
)
from fitness_solutions_server.exercises.models import Exercise
from fitness_solutions_server.fitness_plans.models import FitnessPlan
from fitness_solutions_server.orders.models import Order
from fitness_solutions_server.user_workouts.models import UserWorkout
from fitness_solutions_server.users.models import User

if TYPE_CHECKING:
    from fitness_solutions_server.fitness_coaches.models import FitnessCoach


class SetWeightType(str, Enum):
    absolute = "absolute"
    relative = "relative"


class WorkoutExercise(Base):
    __tablename__ = "workout_exercises"
    __table_args__ = (
        UniqueConstraint(
            "workout_id",
            "order",
            name="workout_exercise_unique_order",
            deferrable=True,
            initially="DEFERRED",
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    workout_id: Mapped[UUID] = mapped_column(
        ForeignKey("workouts.id", ondelete="CASCADE")
    )
    exercise_id: Mapped[UUID] = mapped_column(ForeignKey("exercises.id"))
    order: Mapped[int]

    workout: Mapped["Workout"] = relationship(
        back_populates="workout_exercises", lazy="noload"
    )
    exercise: Mapped[Exercise] = relationship(lazy="noload")
    sets: Mapped[list["WorkoutExerciseSet"]] = relationship(
        back_populates="workout_exercise",
        lazy="noload",
        passive_deletes=True,
        cascade="all, delete",
    )


class WorkoutExerciseSet(Base):
    __tablename__ = "workout_exercise_sets"
    __table_args__ = (
        CheckConstraint(
            "weight_type != 'relative' OR weight BETWEEN 0 AND 1.0",
            name="relative_weight_range",
        ),
        UniqueConstraint(
            "workout_exercise_id",
            "order",
            name="workout_exercise_sets_unique_order",
            deferrable=True,
            initially="DEFERRED",
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    workout_exercise_id: Mapped[UUID] = mapped_column(
        ForeignKey("workout_exercises.id", ondelete="CASCADE")
    )
    weight_type: Mapped[SetWeightType | None]
    reps: Mapped[int | None]
    # calculated_weight: Mapped[float | None] # computed??? use context to fetch user ID
    weight: Mapped[float | None]
    break_: Mapped[int | None] = mapped_column("break")
    duration: Mapped[int | None]
    order: Mapped[int]

    workout_exercise: Mapped[WorkoutExercise] = relationship(back_populates="sets")


class Workout(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "workouts"
    __table_args__ = (
        CheckConstraint(
            "user_id IS NOT NULL OR fitness_coach_id IS NOT NULL",
            name="workouts_must_have_owner",
        ),
        CheckConstraint(
            "min_age >= 0 AND min_age <= max_age", name="workout_age_constraints"
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name_translations: Mapped[dict[str, str]] = mapped_column(
        MutableDict.as_mutable(JSONB())
    )
    name: Mapped[str] = translation_hybrid(name_translations)
    description_translations: Mapped[dict[str, str]] = mapped_column(
        MutableDict.as_mutable(JSONB())
    )
    description: Mapped[str] = translation_hybrid(description_translations)
    experience_level: Mapped[ExperienceLevel]
    fitness_coach_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("fitness_coaches.id", ondelete="SET NULL"), index=True
    )
    order_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("orders.id", ondelete="SET NULL"), index=True
    )
    user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    is_released: Mapped[bool]
    focus: Mapped[Focus | None]
    target_sex: Mapped[Sex | None]
    is_saved: Mapped[bool | None] = query_expression()
    min_age: Mapped[int | None]
    max_age: Mapped[int | None]

    fitness_coach: Mapped[FitnessCoach | None] = relationship(
        back_populates="workouts", lazy="noload"
    )
    workout_exercises: Mapped[list["WorkoutExercise"]] = relationship(
        back_populates="workout",
        lazy="noload",
        passive_deletes=True,
        cascade="all, delete",
    )
    exercises: AssociationProxy[list[Exercise]] = association_proxy(
        "workout_exercises",
        "exercise",
        creator=lambda exercise_obj: WorkoutExercise(exercise=exercise_obj),
    )
    order: Mapped[Order | None] = relationship(back_populates="workouts", lazy="noload")
    user: Mapped[User | None] = relationship(back_populates="workouts", lazy="noload")
    user_workouts: Mapped[list[UserWorkout]] = relationship(
        back_populates="workout",
        lazy="noload",
        passive_updates=True,
        passive_deletes=True,
        cascade="all, delete",
    )
    # duration: Mapped[int] = column_property(
    #     select(func.coalesce(func.sum(WorkoutExerciseSet.duration), 0))
    #     .join(WorkoutExercise)
    #     .where(WorkoutExercise.workout_id == id)
    #     .correlate_except(WorkoutExerciseSet)
    #     .scalar_subquery()
    # )
    fitness_plans: Mapped[list[FitnessPlan] | None] = relationship(
        primaryjoin="FitnessPlanWeekWorkout.workout_id == Workout.id",
        secondary="join(FitnessPlanWeek, FitnessPlanWeekWorkout, FitnessPlanWeekWorkout.fitness_plan_week_id == FitnessPlanWeek.id)",
        viewonly=True,
        lazy="noload",
    )

    @hybrid_property
    def duration(self) -> int:
        return sum([s.duration or 0 for ex in self.workout_exercises for s in ex.sets])

    @duration.inplace.expression
    @classmethod
    def _duration_expression(cls):
        return type_coerce(
            select(func.sum(WorkoutExerciseSet.duration))
            .join(WorkoutExercise)
            .where(WorkoutExercise.workout_id == cls.id),
            Integer,
        )

    @hybrid_property
    def completed_count(self) -> int:
        return len(
            list(filter(lambda el: (el.completed_at is not None), self.user_workouts))
        )

    @completed_count.inplace.expression
    @classmethod
    def _completed_count_expression(cls):
        return type_coerce(
            select(func.count())
            .select_from(UserWorkout)
            .where(UserWorkout.workout_id == cls.id)
            .where(UserWorkout.completed_at.is_not(None))
            .scalar_subquery(),
            Integer,
        )
