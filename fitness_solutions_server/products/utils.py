from typing import Sequence
from uuid import UUID

from fitness_solutions_server.currencies.schemas import Currency
from fitness_solutions_server.images.models import Image
from fitness_solutions_server.storage.base import StorageService

from . import models, schemas


def make_product_image_path(id: UUID, image: Image) -> str:
    return f"products/{id}{image.file_extension}"


def product_model_to_schema(
    product: models.Product, is_admin: bool, storage_service: StorageService
) -> schemas.ProductAdmin | schemas.Product:
    schema = schemas.Product(
        id=product.id,
        name=product.name,
        description=product.description,
        price=product.price,
        discount=product.discount,
        image_url=storage_service.link(product.image_path),
        url=product.url,
        currency=Currency.from_orm(product.currency),
        created_at=product.created_at,
        updated_at=product.updated_at,
        discount_price=product.discount_price,
        brand=product.brand,
    )

    if is_admin:
        schema = schemas.ProductAdmin(
            **schema.dict(),
            name_translations=product.name_translations,
            description_translations=product.description_translations,
            brand_translations=product.brand_translations,
        )

    return schema


def products_model_to_schema(
    products: Sequence[models.Product],
    is_admin: bool,
    storage_service: StorageService,
) -> list[schemas.ProductAdmin] | list[schemas.Product]:
    return [
        product_model_to_schema(
            product=product,
            is_admin=is_admin,
            storage_service=storage_service,
        )
        for product in products
    ]
