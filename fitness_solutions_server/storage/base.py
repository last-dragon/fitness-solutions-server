from abc import ABC, abstractmethod
from typing import Annotated

from fastapi import Depends

from fitness_solutions_server.core.config import settings


class StorageService(ABC):
    @abstractmethod
    async def upload(self, bytes: bytes, path: str):
        pass

    @abstractmethod
    def link(self, path: str) -> str:
        pass

    @abstractmethod
    async def move(self, from_path: str, to_path: str):
        pass


def get_storage_service() -> StorageService:
    from fitness_solutions_server.storage.gcp import GoogleCloudStorageService

    return GoogleCloudStorageService(
        project_id=settings.GOOGLE_CLOUD_PROJECT,
        bucket_name=settings.GOOGLE_CLOUD_STORAGE_BUCKET,
    )
    # return LocalStorageService("/tmp/fitness-solutions-server/images")


StorageServiceDependency = Annotated[StorageService, Depends(get_storage_service)]
