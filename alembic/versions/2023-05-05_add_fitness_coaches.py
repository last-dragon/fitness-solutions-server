"""Add fitness coaches

Revision ID: 925f9627cc32
Revises: 7cfee333fb67
Create Date: 2023-05-05 19:52:15.423469

"""
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "925f9627cc32"
down_revision = "7cfee333fb67"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "countries",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("iso", sa.CHAR(length=2), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "fitness_coaches",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("full_name", sa.String(), nullable=False),
        sa.Column("email", postgresql.CITEXT(), nullable=False),
        sa.Column("password_hash", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=False),
        sa.Column(
            "sex", postgresql.ENUM(name="sex", create_type=False), nullable=False
        ),
        sa.Column("activation_token", sa.String(), nullable=True),
        sa.Column("activated_at", sa.TIMESTAMP(timezone=True), nullable=True),
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
        sa.UniqueConstraint("activation_token"),
        sa.UniqueConstraint("email"),
    )
    op.create_table(
        "fitness_coach_authentication_tokens",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("token", sa.String(), nullable=False),
        sa.Column("fitness_coach_id", sa.Uuid(), nullable=False),
        sa.Column("expires_at", sa.TIMESTAMP(timezone=True), nullable=False),
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
            ["fitness_coach_id"], ["fitness_coaches.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token"),
    )
    op.create_index(
        op.f("ix_fitness_coach_authentication_tokens_fitness_coach_id"),
        "fitness_coach_authentication_tokens",
        ["fitness_coach_id"],
        unique=False,
    )
    op.create_table(
        "fitness_coach_countries",
        sa.Column("fitness_coach_id", sa.Uuid(), nullable=False),
        sa.Column("country_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["country_id"], ["countries.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["fitness_coach_id"], ["fitness_coaches.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("fitness_coach_id", "country_id"),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("fitness_coach_countries")
    op.drop_index(
        op.f("ix_fitness_coach_authentication_tokens_fitness_coach_id"),
        table_name="fitness_coach_authentication_tokens",
    )
    op.drop_table("fitness_coach_authentication_tokens")
    op.drop_table("fitness_coaches")
    op.drop_table("countries")
    # ### end Alembic commands ###
