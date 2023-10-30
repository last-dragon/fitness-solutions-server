from uuid import UUID

from pydantic import BaseModel


class Country(BaseModel):
    id: UUID
    name: str
    iso: str

    class Config:
        orm_mode = True
