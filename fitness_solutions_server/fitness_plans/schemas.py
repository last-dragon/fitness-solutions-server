import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field, validator

from fitness_solutions_server.core.localization import TranslationDict
from fitness_solutions_server.core.models import ExperienceLevel, Focus, Sex, Weekday
from fitness_solutions_server.core.schemas import TimestampMixin
from fitness_solutions_server.equipment.schemas import Equipment
from fitness_solutions_server.fitness_coaches.schemas import FitnessCoach
from fitness_solutions_server.muscle_groups.schemas import MuscleGroup
from fitness_solutions_server.user_workouts.schemas import UserWorkout


class FitnessPlanSortBy(str, Enum):
    created_at = "created_at"
    participants_count = "participants_count"


class FitnessPlanEmbed(str, Enum):
    fitness_coach = "fitness_coach"
    muscle_groups = "muscle_groups"
    equipment = "equipment"


class FitnessPlanCreate(BaseModel):
    name_translations: TranslationDict
    description_translations: TranslationDict
    experience_level: ExperienceLevel
    order_id: UUID
    number_of_workouts_per_week: int = Field(gt=0)
    focus: Focus | None
    target_sex: Sex | None
    min_age: int | None = Field(ge=0)
    max_age: int | None = Field(ge=0)

    @validator("max_age")
    def validate_age(cls, v, values):
        if values["min_age"] is not None and values["min_age"] > v:
            raise ValueError("must be greather than or equal to min_age")

        return v


class FitnessPlanBase(TimestampMixin, BaseModel):
    id: UUID
    name: str
    description: str
    experience_level: ExperienceLevel
    number_of_workouts_per_week: int
    fitness_coach_id: UUID
    focus: Focus | None
    target_sex: Sex | None
    min_age: int | None
    max_age: int | None
    fitness_coach: FitnessCoach | None
    muscle_groups: list[MuscleGroup] | None
    equipment: list[Equipment] | None
    is_saved: bool | None
    is_released: bool

    class Config:
        orm_mode = True


class FitnessPlanUpdate(BaseModel):
    name_translations: TranslationDict | None
    description_translations: TranslationDict | None
    experience_level: ExperienceLevel | None
    number_of_workouts_per_week: int | None = Field(gt=0)
    focus: Focus | None = Field(nullable=True)
    target_sex: Sex | None = Field(nullable=True)
    min_age: int | None = Field(ge=0, nullable=True)
    max_age: int | None = Field(ge=0, nullable=True)
    is_released: bool | None

    @validator("max_age")
    def validate_age(cls, v, values):
        if values["min_age"] is not None and values["min_age"] > v:
            raise ValueError("must be greather than or equal to min_age")

        return v


class FitnessPlanPublic(FitnessPlanBase):
    pass


class FitnessPlanPrivate(FitnessPlanBase):
    name_translations: TranslationDict
    description_translations: TranslationDict
    order_id: UUID


class FitnessPlanWeek(TimestampMixin, BaseModel):
    id: UUID
    fitness_plan_id: UUID
    order: int

    class Config:
        orm_mode = True


class FitnessPlanWeekWorkoutCreate(BaseModel):
    workout_id: UUID


class FitnessPlanWeekWorkout(TimestampMixin, BaseModel):
    id: UUID
    workout_id: UUID
    fitness_plan_week_id: UUID
    order: int

    class Config:
        orm_mode = True


class FitnessPlanParticipationCreate(BaseModel):
    fitness_plan_id: UUID
    days: set[Weekday]


class FitnessPlanParticipation(TimestampMixin, BaseModel):
    id: UUID
    started_at: datetime.date
    user_id: UUID
    fitness_plan_id: UUID
    is_active: bool

    class Config:
        orm_mode = True


class FitnessPlanParticipationUpdate(BaseModel):
    is_active: bool | None = Field(
        description="Can only be set from `true` to `false` to leave a fitness plan"
    )


class WeekStatus(str, Enum):
    none = "none"
    pending = "pending"
    missed = "missed"
    done = "done"


class FitnessPlanWeekStatus(BaseModel):
    monday: WeekStatus
    tuesday: WeekStatus
    wednesday: WeekStatus
    thursday: WeekStatus
    friday: WeekStatus
    saturday: WeekStatus
    sunday: WeekStatus


class FitnessPlanActive(FitnessPlanPublic):
    todays_workout: UserWorkout | None
    week_status: FitnessPlanWeekStatus
    participation_id: UUID

    class Config:
        orm_mode = True
