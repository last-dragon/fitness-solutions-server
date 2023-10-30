from __future__ import annotations

from uuid import UUID, uuid4

from sqlalchemy import ForeignKey, Index, func, select
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import Mapped, column_property, mapped_column, relationship

from fitness_solutions_server.core.localization import translation_hybrid
from fitness_solutions_server.core.models import Base, TimestampMixin
from fitness_solutions_server.fitness_coaches.models import FitnessCoach
from fitness_solutions_server.fitness_plans.models import FitnessPlan
from fitness_solutions_server.products.models import Product
from fitness_solutions_server.workouts.models import Workout


class CollectionItem(TimestampMixin, Base):
    __tablename__ = "collection_items"
    __mapper_args__ = {
        "polymorphic_identity": "collection_item",
        "polymorphic_on": "type",
    }

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    type: Mapped[str]
    collection_id: Mapped[UUID] = mapped_column(
        ForeignKey("collections.id", ondelete="CASCADE"), index=True
    )
    collection: Mapped[Collection] = relationship(back_populates="items")


class Collection(TimestampMixin, Base):
    __tablename__ = "collections"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    title_translations: Mapped[dict[str, str]] = mapped_column(
        MutableDict.as_mutable(JSONB())
    )
    title: Mapped[str] = translation_hybrid(title_translations)
    subtitle_translations: Mapped[dict[str, str]] = mapped_column(
        MutableDict.as_mutable(JSONB())
    )
    subtitle: Mapped[str] = translation_hybrid(subtitle_translations)
    cover_image_path: Mapped[str]
    is_released: Mapped[bool]
    items: Mapped[list["CollectionItem"]] = relationship(
        back_populates="collection",
        cascade="all, delete",
        passive_deletes=True,
        lazy="noload",
    )
    number_of_workouts: Mapped[int] = column_property(
        select(func.count(CollectionItem.id))
        .where(CollectionItem.collection_id == id)
        .where(CollectionItem.type == "collection_item_workout")
        .correlate_except(CollectionItem)
        .scalar_subquery()
    )
    number_of_fitness_plans: Mapped[int] = column_property(
        select(func.count(CollectionItem.id))
        .where(CollectionItem.collection_id == id)
        .where(CollectionItem.type == "collection_item_fitness_plan")
        .correlate_except(CollectionItem)
        .scalar_subquery()
    )
    number_of_fitness_coaches: Mapped[int] = column_property(
        select(func.count(CollectionItem.id))
        .where(CollectionItem.collection_id == id)
        .where(CollectionItem.type == "collection_item_fitness_coach")
        .correlate_except(CollectionItem)
        .scalar_subquery()
    )
    number_of_products: Mapped[int] = column_property(
        select(func.count(CollectionItem.id))
        .where(CollectionItem.collection_id == id)
        .where(CollectionItem.type == "collection_item_product")
        .correlate_except(CollectionItem)
        .scalar_subquery()
    )


class CollectionItemWorkout(CollectionItem):
    __tablename__ = "collections_items_workouts"
    __table_args__ = (Index(None, "collection_id", "workout_id", unique=True),)
    __mapper_args__ = {"polymorphic_identity": "collection_item_workout"}

    id: Mapped[UUID] = mapped_column(
        ForeignKey("collection_items.id"), primary_key=True
    )
    workout_id: Mapped[UUID] = mapped_column(
        ForeignKey("workouts.id", ondelete="CASCADE")
    )
    workout: Mapped[Workout] = relationship(lazy="noload")

    # Duplicate for UNIQUE constraint
    collection_id: Mapped[UUID] = mapped_column(
        ForeignKey("collections.id", ondelete="CASCADE"), use_existing_column=True
    )


class CollectionItemFitnessPlan(CollectionItem):
    __tablename__ = "collections_items_fitness_plans"
    __table_args__ = (Index(None, "collection_id", "fitness_plan_id", unique=True),)
    __mapper_args__ = {"polymorphic_identity": "collection_item_fitness_plan"}

    id: Mapped[UUID] = mapped_column(
        ForeignKey("collection_items.id"), primary_key=True
    )
    fitness_plan_id: Mapped[UUID] = mapped_column(
        ForeignKey("fitness_plans.id", ondelete="CASCADE")
    )
    fitness_plan: Mapped[FitnessPlan] = relationship(lazy="noload")

    # Duplicate for UNIQUE constraint
    collection_id: Mapped[UUID] = mapped_column(
        ForeignKey("collections.id", ondelete="CASCADE"), use_existing_column=True
    )


class CollectionItemFitnessCoach(CollectionItem):
    __tablename__ = "collections_items_fitness_coaches"
    __table_args__ = (Index(None, "collection_id", "fitness_coach_id", unique=True),)
    __mapper_args__ = {"polymorphic_identity": "collection_item_fitness_coach"}

    id: Mapped[UUID] = mapped_column(
        ForeignKey("collection_items.id"), primary_key=True
    )
    fitness_coach_id: Mapped[UUID] = mapped_column(
        ForeignKey("fitness_coaches.id", ondelete="CASCADE")
    )
    fitness_coach: Mapped[FitnessCoach] = relationship(lazy="noload")

    # Duplicate for UNIQUE constraint
    collection_id: Mapped[UUID] = mapped_column(
        ForeignKey("collections.id", ondelete="CASCADE"), use_existing_column=True
    )


class CollectionItemProduct(CollectionItem):
    __tablename__ = "collections_items_products"
    __table_args__ = (Index(None, "collection_id", "product_id", unique=True),)
    __mapper_args__ = {"polymorphic_identity": "collection_item_product"}

    id: Mapped[UUID] = mapped_column(
        ForeignKey("collection_items.id"), primary_key=True
    )
    product_id: Mapped[UUID] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE")
    )
    product: Mapped[Product] = relationship(lazy="noload")

    # Duplicate for UNIQUE constraint
    collection_id: Mapped[UUID] = mapped_column(
        ForeignKey("collections.id", ondelete="CASCADE"), use_existing_column=True
    )
