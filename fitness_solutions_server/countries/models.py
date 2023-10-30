from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import CHAR
from sqlalchemy.orm import Mapped, mapped_column, relationship

from fitness_solutions_server.core.models import Base

if TYPE_CHECKING:
    from fitness_solutions_server.users.models import User


class Country(Base):
    __tablename__ = "countries"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str]
    iso: Mapped[str] = mapped_column(CHAR(length=2))

    users: Mapped["User"] = relationship(back_populates="country", lazy="noload")
