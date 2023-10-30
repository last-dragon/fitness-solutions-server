from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import CHAR, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import Mapped, mapped_column, relationship

from fitness_solutions_server.core.localization import translation_hybrid
from fitness_solutions_server.core.models import Base, TimestampMixin
from fitness_solutions_server.currencies.models import Currency


class Product(TimestampMixin, Base):
    __tablename__ = "products"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name_translations: Mapped[dict[str, str]] = mapped_column(
        MutableDict.as_mutable(JSONB())
    )
    name: Mapped[str] = translation_hybrid(name_translations)
    description_translations: Mapped[dict[str, str]] = mapped_column(
        MutableDict.as_mutable(JSONB())
    )
    description: Mapped[str] = translation_hybrid(description_translations)
    image_path: Mapped[str]
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    discount: Mapped[float | None]
    discount_price: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    brand_translations: Mapped[dict[str, str]] = mapped_column(
        MutableDict.as_mutable(JSONB())
    )
    brand: Mapped[str] = translation_hybrid(brand_translations)
    url: Mapped[str]
    currency_code: Mapped[CHAR] = mapped_column(ForeignKey("currencies.code"))
    currency: Mapped[Currency] = relationship(lazy="joined")
