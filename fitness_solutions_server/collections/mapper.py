from typing import Annotated, Sequence

from fastapi import Depends

from fitness_solutions_server.admins.dependencies import IsAdminDependency
from fitness_solutions_server.storage.base import StorageServiceDependency

from . import models, schemas


class CollectionMapper:
    def __init__(
        self, is_admin: IsAdminDependency, storage_service: StorageServiceDependency
    ):
        self.storage_service = storage_service
        self.is_admin = is_admin

    def collection_to_schema(
        self,
        collection: models.Collection,
    ) -> schemas.CollectionAdmin | schemas.Collection:
        base_schema = schemas.Collection(
            id=collection.id,
            title=collection.title,
            subtitle=collection.subtitle,
            cover_image_url=self.storage_service.link(path=collection.cover_image_path),
            created_at=collection.created_at,
            updated_at=collection.updated_at,
            number_of_workouts=collection.number_of_workouts,
            number_of_fitness_plans=collection.number_of_fitness_plans,
            number_of_fitness_coaches=collection.number_of_fitness_coaches,
            number_of_products=collection.number_of_products,
        )

        if self.is_admin:
            base_schema = schemas.CollectionAdmin(
                **base_schema.dict(),
                title_translations=collection.title_translations,
                subtitle_translations=collection.subtitle_translations,
                is_released=collection.is_released,
            )

        return base_schema

    def collections_to_schema(
        self, collections: Sequence[models.Collection]
    ) -> list[schemas.CollectionAdmin] | list[schemas.Collection]:
        return [self.collection_to_schema(collection) for collection in collections]


CollectionMapperDependency = Annotated[CollectionMapper, Depends()]
