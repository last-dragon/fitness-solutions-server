from enum import Enum
from typing import Annotated, Literal, Union
from uuid import UUID

from pydantic import BaseModel, Field

from fitness_solutions_server.core.localization import TranslationDict
from fitness_solutions_server.core.schemas import TimestampMixin
from fitness_solutions_server.fitness_coaches.schemas import FitnessCoach
from fitness_solutions_server.fitness_plans.schemas import FitnessPlanPublic
from fitness_solutions_server.products.schemas import Product
from fitness_solutions_server.workouts.schemas import Workout


class ItemType(str, Enum):
    workout = "workout"
    fitness_plan = "fitness_plan"
    fitness_coach = "fitness_coach"
    product = "product"


class CollectionItemEmbed(str, Enum):
    item = "item"


class CollectionCreate(BaseModel):
    title_translations: TranslationDict
    subtitle_translations: TranslationDict
    cover_image_id: UUID
    is_released: bool


class CollectionUpdate(BaseModel):
    title_translations: TranslationDict | None
    subtitle_translations: TranslationDict | None
    cover_image_id: UUID | None
    is_released: bool | None


class Collection(TimestampMixin, BaseModel):
    id: UUID
    title: str
    subtitle: str
    cover_image_url: str
    number_of_workouts: int
    number_of_fitness_plans: int
    number_of_fitness_coaches: int
    number_of_products: int


class CollectionAdmin(Collection):
    title_translations: TranslationDict
    subtitle_translations: TranslationDict
    is_released: bool


class AddItemRequest(BaseModel):
    type: ItemType
    item_id: UUID


class CollectionItemWorkout(TimestampMixin, BaseModel):
    id: UUID
    type: Literal[ItemType.workout] = ItemType.workout
    workout_id: UUID
    workout: Workout | None


class CollectionItemFitnessPlan(TimestampMixin, BaseModel):
    id: UUID
    type: Literal[ItemType.fitness_plan] = ItemType.fitness_plan
    fitness_plan_id: UUID
    fitness_plan: FitnessPlanPublic | None


class CollectionItemFitnessCoach(TimestampMixin, BaseModel):
    id: UUID
    type: Literal[ItemType.fitness_coach] = ItemType.fitness_coach
    fitness_coach_id: UUID
    fitness_coach: FitnessCoach | None


class CollectionItemProduct(TimestampMixin, BaseModel):
    id: UUID
    type: Literal[ItemType.product] = ItemType.product
    product_id: UUID
    product: Product | None


CollectionItem = Annotated[
    Union[
        CollectionItemWorkout,
        CollectionItemFitnessPlan,
        CollectionItemFitnessCoach,
        CollectionItemProduct,
    ],
    Field(discriminator="type"),
]
