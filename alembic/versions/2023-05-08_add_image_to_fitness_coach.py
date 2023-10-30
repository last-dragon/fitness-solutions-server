"""Add image to fitness coach

Revision ID: 573120f2bf76
Revises: 08494b28d94f
Create Date: 2023-05-08 17:23:49.851445

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "573120f2bf76"
down_revision = "08494b28d94f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "fitness_coaches", sa.Column("profile_image_path", sa.String(), nullable=False)
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("fitness_coaches", "profile_image_path")
    # ### end Alembic commands ###