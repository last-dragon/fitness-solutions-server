from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import CITEXT
from sqlalchemy.orm import Mapped, mapped_column, relationship

from fitness_solutions_server.core.models import Base, TimestampMixin


class Admin(TimestampMixin, Base):
    __tablename__ = "admins"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    full_name: Mapped[str]
    email: Mapped[str] = mapped_column(CITEXT(), unique=True)
    password_hash: Mapped[str]
    activation_token: Mapped[str | None] = mapped_column(unique=True)
    activated_at: Mapped[datetime | None]

    authentication_tokens: Mapped[list["AdminAuthenticationToken"]] = relationship(
        back_populates="admin", passive_deletes=True
    )


class AdminAuthenticationToken(TimestampMixin, Base):
    __tablename__ = "admin_authentication_tokens"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    token: Mapped[str] = mapped_column(unique=True)
    admin_id: Mapped[UUID] = mapped_column(
        ForeignKey("admins.id", ondelete="CASCADE"), index=True
    )
    expires_at: Mapped[datetime]

    admin: Mapped[Admin] = relationship(back_populates="authentication_tokens")
