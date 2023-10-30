from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field, validator

from fitness_solutions_server.core.localization import TranslationDict
from fitness_solutions_server.core.models import ExperienceLevel, Focus, Sex
from fitness_solutions_server.core.schemas import TimestampMixin
from fitness_solutions_server.exercises.schemas import Exercise
from fitness_solutions_server.fitness_coaches.schemas import FitnessCoach
from fitness_solutions_server.workouts.models import SetWeightType


class WorkoutEmbedOption(str, Enum):
    exercises = "exercises"
    fitness_coach = "fitness_coach"


class WorkoutSortBy(str, Enum):
    created_at = "created_at"
    completed_count = "completed_count"


class WorkoutExerciseSetCreate(BaseModel):
    weight_type: SetWeightType | None = Field(
        description="If supplied, you must also specify the `weight` attribute."
    )
    reps: int | None = Field(ge=0)
    weight: float | None = Field(
        description="The weight in kg (if absolute weight) or in percentage between 0 and 1.0 (if relative weight)"
    )
    """ test """
    break_: int | None = Field(alias="break", description="Break in seconds", ge=0)
    duration: int | None = Field(description="Duration in seconds", ge=0)

    @validator("weight", always=True)
    def validate_weight(cls, v, values):
        if values["weight_type"] is not None and v is None:
            raise ValueError("must be supplied when weight_type is specified")

        if values["weight_type"] == SetWeightType.relative and v > 1.0:
            raise ValueError("must be between 0.0 and 1.0")

        return v


class WorkoutExerciseCreate(BaseModel):
    exercise_id: UUID
    sets: list[WorkoutExerciseSetCreate]


class WorkoutCreate(BaseModel):
    name_translations: TranslationDict
    description_translations: TranslationDict
    experience_level: ExperienceLevel
    exercises: list[WorkoutExerciseCreate]
    order_id: UUID | None
    focus: Focus | None = Field(description="Only used for fitness coaches")
    target_sex: Sex | None = Field(description="Only used for fitness coaches")
    min_age: int | None = Field(
        description="Minimum age for this workout, only used for fitness coaches", ge=0
    )
    max_age: int | None = Field(
        description="Maximum age for this workout, only used for fitness coaches, must be greater or equal to min_age",
        ge=0,
    )

    @validator("max_age")
    def validate_age(cls, v, values):
        if values["min_age"] is not None and values["min_age"] > v:
            raise ValueError("must be greather than or equal to min_age")

        return v


class WorkoutUpdate(BaseModel):
    is_released: bool | None
    name_translations: TranslationDict | None
    description_translations: TranslationDict | None
    experience_level: ExperienceLevel | None
    exercises: list[WorkoutExerciseCreate] | None


class WorkoutExerciseSet(BaseModel):
    id: UUID
    weight_type: SetWeightType | None
    reps: int | None
    break_: int | None = Field(alias="break")
    duration: int | None
    order: int
    weight: float | None

    class Config:
        orm_mode = True
        allow_population_by_field_name = True


class WorkoutExercise(BaseModel):
    id: UUID
    exercise: Exercise
    order: int
    sets: list[WorkoutExerciseSet]


class Workout(TimestampMixin, BaseModel):
    id: UUID
    name: str
    description: str
    experience_level: ExperienceLevel
    exercises: list[WorkoutExercise] | None
    user_id: UUID | None
    fitness_coach_id: UUID | None
    fitness_coach: FitnessCoach | None
    focus: Focus | None
    target_sex: Sex | None
    is_saved: bool | None
    min_age: int | None
    max_age: int | None


class WorkoutPrivate(Workout):
    order_id: UUID | None
    is_released: bool
    name_translations: TranslationDict
    description_translations: TranslationDict
