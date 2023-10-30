"""collections

Revision ID: 4dac49dc3bf3
Revises: 4c64aba66100
Create Date: 2023-08-23 10:58:27.268521

"""
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "4dac49dc3bf3"
down_revision = "4c64aba66100"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "collections",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "title_translations",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column(
            "subtitle_translations",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column("cover_image_path", sa.String(), nullable=False),
        sa.Column("is_released", sa.Boolean(), nullable=False),
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
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "collection_items",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("collection_id", sa.Uuid(), nullable=False),
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
        sa.ForeignKeyConstraint(
            ["collection_id"], ["collections.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_collection_items_collection_id"),
        "collection_items",
        ["collection_id"],
        unique=False,
    )
    op.create_table(
        "collections_items_fitness_coaches",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("fitness_coach_id", sa.Uuid(), nullable=False),
        sa.Column("collection_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(
            ["collection_id"], ["collections.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["fitness_coach_id"], ["fitness_coaches.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["id"],
            ["collection_items.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_collections_items_fitness_coaches_collection_id"),
        "collections_items_fitness_coaches",
        ["collection_id", "fitness_coach_id"],
        unique=True,
    )
    op.create_table(
        "collections_items_fitness_plans",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("fitness_plan_id", sa.Uuid(), nullable=False),
        sa.Column("collection_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(
            ["collection_id"], ["collections.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["fitness_plan_id"], ["fitness_plans.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["id"],
            ["collection_items.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_collections_items_fitness_plans_collection_id"),
        "collections_items_fitness_plans",
        ["collection_id", "fitness_plan_id"],
        unique=True,
    )
    op.create_table(
        "collections_items_workouts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("workout_id", sa.Uuid(), nullable=False),
        sa.Column("collection_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(
            ["collection_id"], ["collections.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["id"],
            ["collection_items.id"],
        ),
        sa.ForeignKeyConstraint(["workout_id"], ["workouts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_collections_items_workouts_collection_id"),
        "collections_items_workouts",
        ["collection_id", "workout_id"],
        unique=True,
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(
        op.f("ix_collections_items_workouts_collection_id"),
        table_name="collections_items_workouts",
    )
    op.drop_table("collections_items_workouts")
    op.drop_index(
        op.f("ix_collections_items_fitness_plans_collection_id"),
        table_name="collections_items_fitness_plans",
    )
    op.drop_table("collections_items_fitness_plans")
    op.drop_index(
        op.f("ix_collections_items_fitness_coaches_collection_id"),
        table_name="collections_items_fitness_coaches",
    )
    op.drop_table("collections_items_fitness_coaches")
    op.drop_index(
        op.f("ix_collection_items_collection_id"), table_name="collection_items"
    )
    op.drop_table("collection_items")
    op.drop_table("collections")
    # ### end Alembic commands ###
