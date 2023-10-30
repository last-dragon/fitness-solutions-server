from uuid import UUID

from pydantic import BaseModel

from fitness_solutions_server.core.localization import TranslationDict
from fitness_solutions_server.core.schemas import TimestampMixin
from fitness_solutions_server.muscle_groups.models import BodyPart


class MuscleGroupBase(BaseModel):
    name: str
    body_part: BodyPart


class MuscleGroupCreate(BaseModel):
    image_id: UUID
    name_translations: TranslationDict
    body_part: BodyPart


class MuscleGroupUpdate(BaseModel):
    image_id: UUID | None
    name_translations: TranslationDict | None
    body_part: BodyPart | None


class MuscleGroup(MuscleGroupBase, TimestampMixin):
    id: UUID
    image_url: str


class MuscleGroupAdmin(MuscleGroup):
    name_translations: TranslationDict
