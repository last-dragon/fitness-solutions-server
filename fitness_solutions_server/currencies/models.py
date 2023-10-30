from sqlalchemy import CHAR
from sqlalchemy.orm import Mapped, mapped_column

from fitness_solutions_server.core.models import Base, TimestampMixin


class Currency(Base, TimestampMixin):
    __tablename__ = "currencies"

    code: Mapped[CHAR] = mapped_column(CHAR(3), primary_key=True)
    name: Mapped[str] = mapped_column()
