"""Update workouts

Revision ID: 943e51557d07
Revises: f1168e97f2a9
Create Date: 2023-06-23 15:11:12.837772

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "943e51557d07"
down_revision = "f1168e97f2a9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column("workouts", sa.Column("order_id", sa.Uuid(), nullable=True))
    op.add_column("workouts", sa.Column("user_id", sa.Uuid(), nullable=True))
    op.add_column("workouts", sa.Column("is_released", sa.Boolean(), nullable=False))
    op.create_index(
        op.f("ix_workouts_order_id"), "workouts", ["order_id"], unique=False
    )
    op.create_index(op.f("ix_workouts_user_id"), "workouts", ["user_id"], unique=False)
    op.create_foreign_key(
        None, "workouts", "orders", ["order_id"], ["id"], ondelete="CASCADE"
    )
    op.create_foreign_key(None, "workouts", "users", ["user_id"], ["id"])
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, "workouts", type_="foreignkey")
    op.drop_constraint(None, "workouts", type_="foreignkey")
    op.drop_index(op.f("ix_workouts_user_id"), table_name="workouts")
    op.drop_index(op.f("ix_workouts_order_id"), table_name="workouts")
    op.drop_column("workouts", "is_released")
    op.drop_column("workouts", "user_id")
    op.drop_column("workouts", "order_id")
    # ### end Alembic commands ###
