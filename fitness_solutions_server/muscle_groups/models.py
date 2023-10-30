from enum import Enum
from uuid import UUID, uuid4

from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import Mapped, mapped_column

from fitness_solutions_server.core.localization import translation_hybrid
from fitness_solutions_server.core.models import Base, SoftDeleteMixin, TimestampMixin


class BodyPart(str, Enum):
    upper_body = "upper_body"
    lower_body = "lower_body"
    core = "core"


class MuscleGroup(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "muscle_groups"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name_translations: Mapped[dict[str, str]] = mapped_column(
        MutableDict.as_mutable(JSONB())
    )
    name = translation_hybrid(name_translations)
    image_path: Mapped[str]
    body_part: Mapped[BodyPart]
