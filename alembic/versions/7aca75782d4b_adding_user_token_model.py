"""Adding user token model

Revision ID: 7aca75782d4b
Revises: dbb75d162207
Create Date: 2023-04-13 19:34:17.113070

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "7aca75782d4b"
down_revision = "dbb75d162207"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "user_authentication_tokens",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("token", sa.String(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
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
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token"),
    )
    op.create_unique_constraint(
        "uq:users_verification_code", "users", ["verification_code"]
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint("uq:users_verification_code", "users", type_="unique")
    op.drop_table("user_authentication_tokens")
    # ### end Alembic commands ###
