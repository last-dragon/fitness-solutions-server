"""Add images

Revision ID: 08494b28d94f
Revises: bdd36c5d55a7
Create Date: 2023-05-08 16:52:21.093231

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "08494b28d94f"
down_revision = "bdd36c5d55a7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "images",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("path", sa.String(), nullable=False),
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
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("images")
    # ### end Alembic commands ###