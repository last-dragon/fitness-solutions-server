from sqlalchemy import Column, ForeignKey, Table

from fitness_solutions_server.core.models import Base

user_saved_fitness_plans = Table(
    "user_saved_fitness_plans",
    Base.metadata,
    Column(
        "fitness_plan_id",
        ForeignKey("fitness_plans.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column("user_id", ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
)
