"""delete users and fitness coach

Revision ID: a0bfeef428f8
Revises: 8a0a7d72b04d
Create Date: 2023-07-16 10:53:17.708928

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "a0bfeef428f8"
down_revision = "8a0a7d72b04d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "workouts", sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.drop_constraint("workouts_order_id_fkey", "workouts", type_="foreignkey")
    op.drop_constraint("workouts_fitness_coach_id_fkey", "workouts", type_="foreignkey")
    op.drop_constraint("workouts_user_id_fkey", "workouts", type_="foreignkey")
    op.create_foreign_key(
        None,
        "workouts",
        "fitness_coaches",
        ["fitness_coach_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        None, "workouts", "orders", ["order_id"], ["id"], ondelete="SET NULL"
    )
    op.create_foreign_key(
        None, "workouts", "users", ["user_id"], ["id"], ondelete="CASCADE"
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, "workouts", type_="foreignkey")
    op.drop_constraint(None, "workouts", type_="foreignkey")
    op.drop_constraint(None, "workouts", type_="foreignkey")
    op.create_foreign_key(
        "workouts_user_id_fkey", "workouts", "users", ["user_id"], ["id"]
    )
    op.create_foreign_key(
        "workouts_fitness_coach_id_fkey",
        "workouts",
        "fitness_coaches",
        ["fitness_coach_id"],
        ["id"],
    )
    op.create_foreign_key(
        "workouts_order_id_fkey", "workouts", "orders", ["order_id"], ["id"]
    )
    op.drop_column("workouts", "deleted_at")
    # ### end Alembic commands ###
