import os
from uuid import UUID, uuid4

from sqlalchemy.orm import Mapped, mapped_column

from fitness_solutions_server.core.models import Base, TimestampMixin


class Image(Base, TimestampMixin):
    __tablename__ = "images"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    path: Mapped[str]

    @property
    def file_name(self) -> str:
        return os.path.split(self.path)[1]

    @property
    def file_extension(self) -> str:
        return os.path.splitext(self.file_name)[1]
