from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Union
from uuid import UUID
from xmlrpc.client import boolean

from pydantic import BaseModel, Field

from fitness_solutions_server.core.localization import TranslationDict
from fitness_solutions_server.core.schemas import TimestampMixin
from fitness_solutions_server.equipment.schemas import Equipment
from fitness_solutions_server.muscle_groups.schemas import MuscleGroup


class ExerciseEmbed(str, Enum):
    latest_personal_record = "latest_personal_record"


class ExerciseListOrderBy(str, Enum):
    muscle_group = "muscle_group"
    id = "id"


class ExerciseCreate(BaseModel):
    name_translations: TranslationDict
    en_name: str
    is_bodyweight: bool
    image_id: UUID
    equipment_ids: set[UUID]
    muscle_groups_ids: set[UUID]
    model_3d_path: Path = Field(
        description="Relative path to 3D model", example="3d_models/mymodel.3ds"
    )


class ExerciseUpdate(BaseModel):
    name_translations: TranslationDict | None
    en_name: str | None
    is_bodyweight: bool | None
    relative_bodyweight_intensity: float | None
    image_id: UUID | None
    equipment_ids: set[UUID] | None
    muscle_groups_ids: set[UUID] | None
    model_3d_path: Path | None = Field(
        description="Relative path to 3D model", example="3d_models/mymodel.3ds"
    )


class ExerciseBase(TimestampMixin, BaseModel):
    id: UUID
    name: str
    en_name: str
    is_bodyweight: bool
    relative_bodyweight_intensity: float | None
    image_url: str
    muscle_groups: list[MuscleGroup]
    equipment: list[Equipment]
    model_3d_url: str
    latest_personal_record: Union["PRObservation", None] = Field(None)


class Exercise(ExerciseBase):
    pass


class ExerciseAdmin(ExerciseBase):
    name_translations: TranslationDict


from fitness_solutions_server.pr_observations.schemas import PRObservation

Exercise.update_forward_refs()
ExerciseBase.update_forward_refs()
ExerciseAdmin.update_forward_refs()
