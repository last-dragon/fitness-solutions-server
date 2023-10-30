from uuid import UUID, uuid4

from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Float

from fitness_solutions_server.core.localization import translation_hybrid
from fitness_solutions_server.core.models import Base, SoftDeleteMixin, TimestampMixin


class Equipment(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "equipment"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name_translations: Mapped[dict[str, str]] = mapped_column(
        MutableDict.as_mutable(JSONB())
    )
    name = translation_hybrid(name_translations)
    consecutive_terms: Mapped[float] = mapped_column(Float)
    image_path: Mapped[str]
