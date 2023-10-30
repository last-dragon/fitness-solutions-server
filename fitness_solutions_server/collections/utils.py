from typing import Sequence, cast
from uuid import UUID

from fitness_solutions_server.collections import models, schemas
from fitness_solutions_server.fitness_coaches.mapper import FitnessCoachMapper
from fitness_solutions_server.fitness_plans.schemas import FitnessPlanPublic
from fitness_solutions_server.fitness_plans.utils import fitness_plan_model_to_schema
from fitness_solutions_server.images.models import Image
from fitness_solutions_server.products.schemas import Product
from fitness_solutions_server.products.utils import product_model_to_schema
from fitness_solutions_server.storage.base import StorageService
from fitness_solutions_server.workouts.utils import workout_model_to_schema


def make_collection_cover_image_path(id: UUID, image: Image) -> str:
    return f"collections/{id}{image.file_extension}"


class InvalidCollectionItemSubType(Exception):
    pass


def collection_item_model_to_schema(
    item: models.CollectionItem,
    is_admin: bool,
    auth_fitness_coach_id: UUID | None,
    storage_service: StorageService,
    fitness_coach_mapper: FitnessCoachMapper,
) -> schemas.CollectionItem:
    base_schema = {
        "id": item.id,
        "created_at": item.created_at,
        "updated_at": item.updated_at,
    }
    is_fitness_coach = auth_fitness_coach_id is not None

    # Ugly pattern matching...
    schema: schemas.CollectionItem
    match item:
        case _ if type(item) == models.CollectionItemWorkout:
            schema = schemas.CollectionItemWorkout(
                **base_schema, workout_id=item.workout_id
            )
            if item.workout is not None:
                schema.workout = workout_model_to_schema(
                    is_admin=is_admin,
                    is_fitness_coach=is_fitness_coach,
                    workout=item.workout,
                    storage_service=storage_service,
                    fitness_coach_mapper=fitness_coach_mapper,
                )
        case _ if type(item) == models.CollectionItemFitnessCoach:
            schema = schemas.CollectionItemFitnessCoach(
                **base_schema, fitness_coach_id=item.fitness_coach_id
            )
            if item.fitness_coach is not None:
                schema.fitness_coach = fitness_coach_mapper.fitness_coach_to_schema(
                    item.fitness_coach
                )
        case _ if type(item) == models.CollectionItemFitnessPlan:
            schema = schemas.CollectionItemFitnessPlan(
                **base_schema, fitness_plan_id=item.fitness_plan_id
            )
            if item.fitness_plan is not None:
                schema.fitness_plan = cast(
                    FitnessPlanPublic,
                    fitness_plan_model_to_schema(
                        is_admin=is_admin,
                        auth_fitness_coach_id=auth_fitness_coach_id,
                        fitness_plan=item.fitness_plan,
                        fitness_coach_mapper=fitness_coach_mapper,
                        storage_service=storage_service,
                    ),
                )
        case _ if type(item) == models.CollectionItemProduct:
            schema = schemas.CollectionItemProduct(
                **base_schema, product_id=item.product_id
            )
            if item.product is not None:
                schema.product = cast(
                    Product,
                    product_model_to_schema(
                        product=item.product,
                        is_admin=is_admin,
                        storage_service=storage_service,
                    ),
                )
        case _:
            raise InvalidCollectionItemSubType()

    return schema


def collection_items_model_to_schema(
    items: Sequence[models.CollectionItem],
    is_admin: bool,
    auth_fitness_coach_id: UUID | None,
    storage_service: StorageService,
    fitness_coach_mapper: FitnessCoachMapper,
) -> list[schemas.CollectionItem]:
    return [
        collection_item_model_to_schema(
            item=item,
            is_admin=is_admin,
            auth_fitness_coach_id=auth_fitness_coach_id,
            storage_service=storage_service,
            fitness_coach_mapper=fitness_coach_mapper,
        )
        for item in items
    ]
