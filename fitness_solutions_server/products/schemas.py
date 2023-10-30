from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl

from fitness_solutions_server.core.localization import TranslationDict
from fitness_solutions_server.core.schemas import TimestampMixin
from fitness_solutions_server.currencies.schemas import Currency


class ProductCreate(BaseModel):
    name_translations: TranslationDict
    description_translations: TranslationDict
    price: Decimal
    discount: Decimal | None = Field(ge=0.0, le=1.0, decimal_places=2)
    discount_price: Decimal | None = Field(ge=0.0)
    brand_translations: TranslationDict
    image_id: UUID
    url: HttpUrl
    currency_code: str = Field(min_length=3, max_length=3)


class ProductUpdate(BaseModel):
    name_translations: TranslationDict | None
    description_translations: TranslationDict | None
    price: Decimal | None
    discount: Decimal | None = Field(ge=0.0, le=1.0, decimal_places=2, nullable=True)
    discount_price: Decimal | None = Field(ge=0.0)
    brand_translations: TranslationDict | None
    # image_id: UUID | None
    url: HttpUrl | None
    currency_code: str | None = Field(min_length=3, max_length=3)


class Product(TimestampMixin, BaseModel):
    id: UUID
    name: str
    description: str
    price: Decimal
    discount: Decimal | None
    discount_price: Decimal | None
    brand: str
    image_url: str
    url: str
    currency: Currency


class ProductAdmin(Product):
    name_translations: TranslationDict
    description_translations: TranslationDict
    brand_translations: TranslationDict
