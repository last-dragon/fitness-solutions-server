from fastapi.concurrency import run_in_threadpool
from google.cloud import storage

from fitness_solutions_server.storage.base import StorageService


class GoogleCloudStorageService(StorageService):
    def __init__(self, project_id: str, bucket_name: str):
        self.client = storage.Client(project=project_id)
        self.bucket = self.client.bucket(bucket_name)

    async def upload(self, bytes: bytes, path: str):
        blob = self.bucket.blob(path)
        await run_in_threadpool(blob.upload_from_string, bytes)
        await run_in_threadpool(blob.make_public)

    def link(self, path: str) -> str:
        return self.bucket.blob(path).public_url

    async def move(self, from_path: str, to_path: str):
        old_blob = self.bucket.blob(from_path)
        new_blob = await run_in_threadpool(self.bucket.rename_blob, old_blob, to_path)
        await run_in_threadpool(new_blob.make_public)
