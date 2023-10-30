from uuid import UUID

from pydantic import BaseModel

from fitness_solutions_server.core.localization import TranslationDict
from fitness_solutions_server.core.schemas import TimestampMixin


class EquipmentBase(BaseModel):
    name: str


class EquipmentCreate(BaseModel):
    image_id: UUID
    consecutive_terms: float
    name_translations: TranslationDict


class EquipmentUpdate(BaseModel):
    image_id: UUID | None
    consecutive_terms: float | None
    name_translations: TranslationDict | None


class Equipment(EquipmentBase, TimestampMixin):
    id: UUID
    image_url: str


class EquipmentAdmin(Equipment):
    name_translations: TranslationDict
    consecutive_terms: float
