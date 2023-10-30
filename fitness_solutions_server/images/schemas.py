from uuid import UUID

from pydantic import BaseModel


class Image(BaseModel):
    id: UUID
