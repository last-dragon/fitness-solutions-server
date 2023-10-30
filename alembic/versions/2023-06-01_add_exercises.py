"""Add exercises

Revision ID: bc06b7d7b17b
Revises: 096487b299b1
Create Date: 2023-06-01 15:04:36.484401

"""
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "bc06b7d7b17b"
down_revision = "096487b299b1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "exercises",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "name_translations", postgresql.JSONB(astext_type=sa.Text()), nullable=False
        ),
        sa.Column("en_name", sa.String(), nullable=False),
        sa.Column("is_bodyweight", sa.Bool(), nullable=False),
        sa.Column("relative_bodyweight_intensity", sa.real(), nullable=True),
        sa.Column("image_path", sa.String(), nullable=False),
        sa.Column("model_3d_path", sa.String(), nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "exercise_equipment",
        sa.Column("exercise_id", sa.Uuid(), nullable=False),
        sa.Column("equipment_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["equipment_id"], ["equipment.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["exercise_id"], ["exercises.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("exercise_id", "equipment_id"),
    )
    op.create_table(
        "exercise_muscle_groups",
        sa.Column("exercise_id", sa.Uuid(), nullable=False),
        sa.Column("muscle_group_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["exercise_id"], ["exercises.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["muscle_group_id"], ["muscle_groups.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("exercise_id", "muscle_group_id"),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("exercise_muscle_groups")
    op.drop_table("exercise_equipment")
    op.drop_table("exercises")
    # ### end Alembic commands ###
