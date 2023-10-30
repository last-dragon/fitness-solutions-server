import functools
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi_pagination import pagination_ctx
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy import select

from fitness_solutions_server.admins.dependencies import (
    IsAdminDependency,
    require_admin_authentication_token,
)
from fitness_solutions_server.collections.models import CollectionItemProduct
from fitness_solutions_server.core.database import DatabaseDependency
from fitness_solutions_server.core.schemas import ResponseModel
from fitness_solutions_server.core.utils import CursorPage, get_or_fail
from fitness_solutions_server.currencies.models import Currency
from fitness_solutions_server.images.models import Image
from fitness_solutions_server.products.utils import (
    make_product_image_path,
    product_model_to_schema,
    products_model_to_schema,
)
from fitness_solutions_server.storage.base import StorageServiceDependency

from . import models, schemas

router = APIRouter(prefix="/products")


@router.post(
    "",
    summary="Create product",
    dependencies=[Depends(require_admin_authentication_token)],
)
async def create_product(
    body: schemas.ProductCreate,
    db: DatabaseDependency,
    storage_service: StorageServiceDependency,
) -> ResponseModel[schemas.ProductAdmin]:
    currency = await get_or_fail(Currency, body.currency_code, db)
    image = await get_or_fail(Image, body.image_id, db)
    product_id = uuid4()
    product_image_path = make_product_image_path(id=product_id, image=image)

    product = models.Product(
        id=product_id,
        name_translations=body.name_translations,
        description_translations=body.description_translations,
        price=body.price,
        currency=currency,
        url=body.url,
        discount=body.discount,
        image_path=product_image_path,
        brand_translations=body.brand_translations,
        discount_price=body.discount_price,
    )
    db.add(product)
    await db.flush()

    # Move image
    await storage_service.move(from_path=image.path, to_path=product_image_path)
    await db.delete(image)

    await db.commit()

    return ResponseModel(
        data=product_model_to_schema(
            product, is_admin=True, storage_service=storage_service
        )
    )


@router.delete(
    "/{product_id}",
    summary="Delete product",
    dependencies=[Depends(require_admin_authentication_token)],
)
async def delete_product(
    product_id: UUID, db: DatabaseDependency
) -> ResponseModel[None]:
    product = await get_or_fail(models.Product, product_id, db)
    await db.delete(product)
    await db.commit()
    return ResponseModel(data=None)


@router.patch(
    "/{product_id}",
    summary="Update product",
    dependencies=[Depends(require_admin_authentication_token)],
)
async def update_product(
    product_id: UUID,
    body: schemas.ProductUpdate,
    db: DatabaseDependency,
    storage_service: StorageServiceDependency,
) -> ResponseModel[schemas.ProductAdmin]:
    product = await get_or_fail(models.Product, product_id, db)
    update_data = body.dict(exclude_unset=True)

    if body.name_translations is not None:
        product.name_translations = body.name_translations
    if body.description_translations is not None:
        product.description_translations = body.description_translations
    if body.price is not None:
        product.price = body.price
    if "discount" in update_data:
        product.discount = update_data["discount"]
    if body.url is not None:
        product.url = body.url
    if body.currency_code is not None:
        currency = await get_or_fail(Currency, body.currency_code, db)
        product.currency = currency
    if body.brand_translations is not None:
        product.brand_translations = body.brand_translations
    if body.discount_price is not None:
        product.discount_price = body.discount_price

    await db.commit()
    return ResponseModel(
        data=product_model_to_schema(
            product, is_admin=True, storage_service=storage_service
        )
    )


@router.get("/{product_id}", summary="Get product by ID")
async def get_product_by_id(
    product_id: UUID, db: DatabaseDependency, storage_service: StorageServiceDependency
) -> ResponseModel[schemas.ProductAdmin | schemas.Product]:
    product = await get_or_fail(models.Product, product_id, db)
    return ResponseModel(
        data=product_model_to_schema(
            product, is_admin=True, storage_service=storage_service
        )
    )


@router.get(
    "", summary="List products", dependencies=[Depends(pagination_ctx(CursorPage))]
)
async def list_products(
    db: DatabaseDependency,
    is_admin: IsAdminDependency,
    storage_service: StorageServiceDependency,
    collection_id: Annotated[UUID | None, Query()] = None,
) -> ResponseModel[CursorPage[schemas.ProductAdmin] | CursorPage[schemas.Product]]:
    query = select(models.Product).order_by(
        models.Product.created_at.desc(), models.Product.id
    )

    if not is_admin and collection_id is None:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, detail="Only admins can see all products"
        )

    if collection_id is not None:
        exists_stmt = (
            select(CollectionItemProduct.id)
            .where(CollectionItemProduct.product_id == models.Product.id)
            .exists()
        )
        query = query.where(
            exists_stmt.where(CollectionItemProduct.collection_id == collection_id)
        )

    products = await paginate(
        db,
        query,
        transformer=functools.partial(
            products_model_to_schema,
            is_admin=is_admin,
            storage_service=storage_service,
        ),
    )

    return ResponseModel(data=products)
