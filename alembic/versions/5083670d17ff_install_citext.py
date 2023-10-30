"""Install CITEXT

Revision ID: 5083670d17ff
Revises:
Create Date: 2023-04-08 11:35:25.228716

"""
import sqlalchemy as sa
from sqlalchemy.sql import text

from alembic import op

# revision identifiers, used by Alembic.
revision = "5083670d17ff"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(text("CREATE EXTENSION IF NOT EXISTS CITEXT;"))
    pass


def downgrade() -> None:
    op.execute(text("DROP EXTENSION IF EXISTS CITEXT;"))
    pass
