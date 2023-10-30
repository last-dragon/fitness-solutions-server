from sqlalchemy import Float
from uuid import UUID, uuid4

from sqlalchemy import Column, ForeignKey, Table, case
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import Mapped, mapped_column, relationship

from fitness_solutions_server.core.localization import translation_hybrid
from fitness_solutions_server.core.models import Base, SoftDeleteMixin, TimestampMixin
from fitness_solutions_server.equipment.models import Equipment
from fitness_solutions_server.muscle_groups.models import BodyPart, MuscleGroup
from fitness_solutions_server.pr_observations.models import PRObservation

exercise_equipment = Table(
    "exercise_equipment",
    Base.metadata,
    Column(
        "exercise_id", ForeignKey("exercises.id", ondelete="CASCADE"), primary_key=True
    ),
    Column(
        "equipment_id", ForeignKey("equipment.id", ondelete="CASCADE"), primary_key=True
    ),
)

exercise_muscle_groups = Table(
    "exercise_muscle_groups",
    Base.metadata,
    Column(
        "exercise_id", ForeignKey("exercises.id", ondelete="CASCADE"), primary_key=True
    ),
    Column(
        "muscle_group_id",
        ForeignKey("muscle_groups.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)

body_part_ordering = {
    BodyPart.upper_body: 0,
    BodyPart.core: 1,
    BodyPart.lower_body: 2,
}


class Exercise(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "exercises"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name_translations: Mapped[dict[str, str]] = mapped_column(
        MutableDict.as_mutable(JSONB())
    )
    name = translation_hybrid(name_translations)
    en_name: Mapped[str]
    is_bodyweight: Mapped[bool]
    relative_bodyweight_intensity: Mapped[float] = mapped_column(Float)
    image_path: Mapped[str]
    model_3d_path: Mapped[str]

    equipment: Mapped[list[Equipment]] = relationship(
        secondary=exercise_equipment, lazy="joined"
    )
    # We add ordering here to that the first one is the one used in list order
    # for exercises.
    muscle_groups: Mapped[list[MuscleGroup]] = relationship(
        secondary=exercise_muscle_groups,
        lazy="joined",
        order_by=[
            case(body_part_ordering, value=MuscleGroup.body_part, else_=99),
            MuscleGroup.name,
        ],
    )
    pr_observations: Mapped[list[PRObservation]] = relationship(
        back_populates="exercise",
        passive_deletes=True,
        cascade="all, delete",
        lazy="noload",
    )
