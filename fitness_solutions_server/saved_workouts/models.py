from sqlalchemy import Column, ForeignKey, Table

from fitness_solutions_server.core.models import Base

user_saved_workouts = Table(
    "user_saved_workouts",
    Base.metadata,
    Column(
        "workout_id", ForeignKey("workouts.id", ondelete="CASCADE"), primary_key=True
    ),
    Column("user_id", ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
)
