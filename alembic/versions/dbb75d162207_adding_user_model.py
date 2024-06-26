"""Adding user model

Revision ID: dbb75d162207
Revises: 5083670d17ff
Create Date: 2023-04-08 17:31:45.392314

"""
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "dbb75d162207"
down_revision = "5083670d17ff"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("email", postgresql.CITEXT(), nullable=False),
        sa.Column("password_hash", sa.String(), nullable=False),
        sa.Column("full_name", sa.String(), nullable=False),
        sa.Column(
            "sex",
            sa.Enum("male", "female", name="sex"),
            nullable=True,
        ),
        sa.Column("height", sa.Float(), nullable=True),
        sa.Column("weight", sa.Float(), nullable=True),
        sa.Column("birthdate", sa.Date(), nullable=True),
        sa.Column(
            "focus",
            sa.Enum("hypertrophy", "strength", "endurance", name="focus"),
            nullable=True,
        ),
        sa.Column("verification_code", sa.String(), nullable=True),
        sa.Column("verified_at", sa.TIMESTAMP(timezone=True), nullable=True),
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
        sa.Column("profile_image_path", sa.String(), nullable=True),
        sa.CheckConstraint("height > 0", name="height_constraint"),
        sa.CheckConstraint("weight > 0", name="weight_constraint"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("users")
    # ### end Alembic commands ###
