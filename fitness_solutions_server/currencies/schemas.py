from pydantic import BaseModel, Field

from fitness_solutions_server.core.schemas import TimestampMixin


class Currency(TimestampMixin, BaseModel):
    code: str = Field(description="ISO 4217 currency code")
    name: str

    class Config:
        orm_mode = True


class CurrencyCreate(BaseModel):
    code: str = Field(description="ISO 4217 currency code")
    name: str
