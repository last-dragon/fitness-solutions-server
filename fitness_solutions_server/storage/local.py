import logging
import os

import aiofiles
from aiofiles import os as aiofiles_os

from fitness_solutions_server.storage.base import StorageService

logger = logging.getLogger(__name__)


class LocalStorageService(StorageService):
    def __init__(self, base_path: str):
        self.base_path = base_path

    async def upload(self, bytes: bytes, path: str):
        path = os.path.join(self.base_path, path)
        logger.debug(f'Uploading file to "{path}"')

        await aiofiles_os.makedirs(os.path.dirname(path), exist_ok=True)

        async with aiofiles.open(os.path.join(self.base_path, path), "wb") as out_file:
            await out_file.write(bytes)

    def link(self, path: str) -> str:
        return os.path.join(self.base_path, path)

    async def move(self, from_path: str, to_path: str):
        from_path = os.path.join(self.base_path, from_path)
        to_path = os.path.join(self.base_path, to_path)
        logger.debug(f'Moving file "{from_path}" to "{to_path}"')

        await aiofiles_os.makedirs(os.path.dirname(to_path), exist_ok=True)
        await aiofiles_os.replace(from_path, to_path)
