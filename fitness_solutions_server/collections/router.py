import functools
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Query
from fastapi_pagination import pagination_ctx
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy import select, true
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectin_polymorphic, selectinload
from sqlalchemy.orm.interfaces import ORMOption

from fitness_solutions_server.admins.dependencies import (
    IsAdminDependency,
    require_admin_authentication_token,
)
from fitness_solutions_server.collections.mapper import CollectionMapperDependency
from fitness_solutions_server.collections.utils import (
    collection_items_model_to_schema,
    make_collection_cover_image_path,
)
from fitness_solutions_server.core.database import DatabaseDependency
from fitness_solutions_server.core.schemas import ResponseModel
from fitness_solutions_server.core.utils import CursorPage, get_or_fail
from fitness_solutions_server.fitness_coaches.dependencies import (
    GetFitnessCoachDependency,
)
from fitness_solutions_server.fitness_coaches.mapper import FitnessCoachMapperDependency
from fitness_solutions_server.fitness_coaches.models import FitnessCoach
from fitness_solutions_server.fitness_plans.models import FitnessPlan
from fitness_solutions_server.images.models import Image
from fitness_solutions_server.products.models import Product
from fitness_solutions_server.storage.base import StorageServiceDependency
from fitness_solutions_server.workouts.models import Workout

from . import models, schemas

CollectionItemEmbedQuery = Annotated[set[schemas.CollectionItemEmbed] | None, Query()]
router = APIRouter(prefix="/collections")


@router.post(
    "",
    summary="Create collection",
    dependencies=[Depends(require_admin_authentication_token)],
)
async def create_collection(
    body: schemas.CollectionCreate,
    db: DatabaseDependency,
    storage_service: StorageServiceDependency,
    mapper: CollectionMapperDependency,
) -> ResponseModel[schemas.CollectionAdmin]:
    cover_image = await get_or_fail(Image, body.cover_image_id, db)
    collection_id = uuid4()
    collection_cover_image_path = make_collection_cover_image_path(
        id=collection_id, image=cover_image
    )
    collection = models.Collection(
        title_translations=body.title_translations,
        subtitle_translations=body.subtitle_translations,
        cover_image_path=collection_cover_image_path,
        is_released=body.is_released,
        number_of_workouts=0,
        number_of_fitness_plans=0,
        number_of_fitness_coaches=0,
        number_of_products=0,
    )
    db.add(collection)
    await db.flush()

    await storage_service.move(
        from_path=cover_image.path, to_path=collection_cover_image_path
    )
    await db.delete(cover_image)
    await db.commit()

    return ResponseModel(data=mapper.collection_to_schema(collection))


@router.get("/{collection_id}", summary="Get collection by ID")
async def get_collection_by_id(
    collection_id: UUID, db: DatabaseDependency, mapper: CollectionMapperDependency
) -> ResponseModel[schemas.CollectionAdmin | schemas.Collection]:
    collection = await get_or_fail(models.Collection, collection_id, db)
    return ResponseModel(data=mapper.collection_to_schema(collection))


@router.patch(
    "/{collection_id}", dependencies=[Depends(require_admin_authentication_token)]
)
async def update_collection(
    collection_id: UUID,
    body: schemas.CollectionUpdate,
    db: DatabaseDependency,
    mapper: CollectionMapperDependency,
    storage_service: StorageServiceDependency,
) -> ResponseModel[schemas.CollectionAdmin]:
    collection = await get_or_fail(models.Collection, collection_id, db)

    if body.title_translations is not None:
        collection.title_translations = body.title_translations

    if body.subtitle_translations is not None:
        collection.subtitle_translations = body.subtitle_translations

    if body.cover_image_id is not None:
        image = await get_or_fail(Image, body.cover_image_id, db)
        collection.cover_image_path = make_collection_cover_image_path(
            id=collection_id, image=image
        )
        await storage_service.move(
            from_path=image.path, to_path=collection.cover_image_path
        )
        await db.delete(image)
    if body.is_released is not None:
        collection.is_released = body.is_released

    # Commit removes column properties
    schema = mapper.collection_to_schema(collection)

    await db.commit()

    return ResponseModel(data=schema)


@router.get(
    "", summary="List collections", dependencies=[Depends(pagination_ctx(CursorPage))]
)
async def list_collections(
    db: DatabaseDependency,
    is_admin: IsAdminDependency,
    mapper: CollectionMapperDependency,
) -> ResponseModel[CursorPage[schemas.CollectionAdmin | schemas.Collection]]:
    query = select(models.Collection).order_by(
        models.Collection.created_at.desc(), models.Collection.id
    )

    if not is_admin:
        query = query.where(models.Collection.is_released == true())

    collections = await paginate(
        db,
        query,
        transformer=functools.partial(mapper.collections_to_schema),
    )

    return ResponseModel(data=collections)


@router.put(
    "/{collection_id}/items",
    summary="Add item to collection",
    dependencies=[Depends(require_admin_authentication_token)],
)
async def add_item(
    collection_id: UUID, body: schemas.AddItemRequest, db: DatabaseDependency
) -> ResponseModel[None]:
    collection = await get_or_fail(models.Collection, collection_id, db)
    item: models.CollectionItem

    match body.type:
        case schemas.ItemType.workout:
            await get_or_fail(Workout, body.item_id, db)
            item = models.CollectionItemWorkout(workout_id=body.item_id)
        case schemas.ItemType.fitness_plan:
            await get_or_fail(FitnessPlan, body.item_id, db)
            item = models.CollectionItemFitnessPlan(fitness_plan_id=body.item_id)
        case schemas.ItemType.fitness_coach:
            await get_or_fail(FitnessCoach, body.item_id, db)
            item = models.CollectionItemFitnessCoach(fitness_coach_id=body.item_id)
        case schemas.ItemType.product:
            await get_or_fail(Product, body.item_id, db)
            item = models.CollectionItemProduct(product_id=body.item_id)

    collection.items.append(item)

    try:
        await db.commit()
    except IntegrityError:
        # We should really use ON CONFLICT DO NOTHING, but that just too much work to add the polymorphism
        pass

    return ResponseModel(data=None)


@router.get(
    "/{collection_id}/items",
    summary="List collection items",
    dependencies=[Depends(pagination_ctx(CursorPage))],
)
async def list_items(
    collection_id: UUID,
    db: DatabaseDependency,
    is_admin: IsAdminDependency,
    fitness_coach: GetFitnessCoachDependency,
    storage_service: StorageServiceDependency,
    fitness_coach_mapper: FitnessCoachMapperDependency,
    embed: CollectionItemEmbedQuery = None,
) -> ResponseModel[CursorPage[schemas.CollectionItem]]:
    collection = await get_or_fail(models.Collection, collection_id, db)
    options: list[ORMOption] = [
        selectin_polymorphic(
            models.CollectionItem,
            [
                models.CollectionItemFitnessCoach,
                models.CollectionItemFitnessPlan,
                models.CollectionItemWorkout,
                models.CollectionItemProduct,
            ],
        ),
    ]

    query = (
        select(models.CollectionItem)
        .where(models.CollectionItem.collection_id == collection.id)
        .order_by(models.CollectionItem.created_at.desc(), models.CollectionItem.id)
    )

    if embed is not None:
        if schemas.CollectionItemEmbed.item in embed:
            options.append(
                selectinload(models.CollectionItemFitnessCoach.fitness_coach)
            )
            options.append(selectinload(models.CollectionItemFitnessPlan.fitness_plan))
            options.append(selectinload(models.CollectionItemWorkout.workout))
            options.append(selectinload(models.CollectionItemProduct.product))

    query = query.options(*options)
    items = await paginate(
        db,
        query,
        transformer=functools.partial(
            collection_items_model_to_schema,
            is_admin=is_admin,
            auth_fitness_coach_id=fitness_coach.id
            if fitness_coach is not None
            else None,
            storage_service=storage_service,
            fitness_coach_mapper=fitness_coach_mapper,
        ),
    )

    return ResponseModel(data=items)


@router.delete(
    "/{collection_id}/items/{item_id}",
    summary="Delete item from collection",
    dependencies=[Depends(require_admin_authentication_token)],
)
async def delete(
    collection_id: UUID, item_id: UUID, db: DatabaseDependency
) -> ResponseModel[None]:
    item = await get_or_fail(models.CollectionItem, item_id, db)
    await db.delete(item)
    await db.commit()
    return ResponseModel(data=None)
