from datetime import datetime
from enum import Enum
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field
from pydantic.generics import GenericModel


class TimestampMixin(BaseModel):
    created_at: datetime
    updated_at: datetime


class SortOrder(str, Enum):
    asc = "asc"
    desc = "desc"


T = TypeVar("T")


class ErrorDetail(BaseModel):
    code: str | None
    detail: Any


class ErrorResponse(BaseModel):
    success: bool = Field(False, const=False)
    message: str
    error: ErrorDetail


class ResponseModel(GenericModel, Generic[T]):
    data: T | None
    success: bool = Field(True, const=True)
    message: str = "OK"
