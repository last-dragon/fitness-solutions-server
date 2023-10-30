from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from fitness_solutions_server.core.models import Base, TimestampMixin

if TYPE_CHECKING:
    from fitness_solutions_server.users.models import User


class WeightLog(Base, TimestampMixin):
    __tablename__ = "weight_logs"
    __table_args__ = (Index(None, "user_id", "created_at"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    weight: Mapped[float]

    user: Mapped["User"] = relationship(back_populates="weight_logs", lazy="noload")
