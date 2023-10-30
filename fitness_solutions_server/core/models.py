import functools
from datetime import datetime
from enum import Enum

from sqlalchemy import TIMESTAMP, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy_easy_softdelete.mixin import generate_soft_delete_mixin_class


class Base(DeclarativeBase):
    type_annotation_map = {datetime: TIMESTAMP(timezone=True)}
    __mapper_args__ = {"eager_defaults": True}


class SoftDeleteMixin(generate_soft_delete_mixin_class()):  # type: ignore
    deleted_at: Mapped[datetime | None]


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )


class ExperienceLevel(str, Enum):
    beginner = "beginner"
    intermediate = "intermediate"
    experienced = "experienced"


class Sex(str, Enum):
    male = "male"
    female = "female"


class Focus(str, Enum):
    hypertrophy = "hypertrophy"
    strength = "strength"
    endurance = "endurance"


@functools.total_ordering
class Weekday(str, Enum):
    monday = "monday"
    tuesday = "tuesday"
    wednesday = "wednesday"
    thursday = "thursday"
    friday = "friday"
    saturday = "saturday"
    sunday = "sunday"

    def numeric_value(cls) -> int:
        match cls:
            case Weekday.monday:
                return 0
            case Weekday.tuesday:
                return 1
            case Weekday.wednesday:
                return 2
            case Weekday.thursday:
                return 3
            case Weekday.friday:
                return 4
            case Weekday.saturday:
                return 5
            case Weekday.sunday:
                return 6

    @classmethod
    @functools.lru_cache(None)
    def _member_list(cls):
        return list(cls)

    def __lt__(self, other):
        if self.__class__ is other.__class__:
            member_list = self.__class__._member_list()
            return member_list.index(self) < member_list.index(other)
        return NotImplemented
