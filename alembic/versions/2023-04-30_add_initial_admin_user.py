"""Add initial admin user

Revision ID: 7cfee333fb67
Revises: 50e1e4c5bd8c
Create Date: 2023-04-30 12:40:31.642474

"""
from uuid import uuid4

from sqlalchemy.orm import Session
from sqlalchemy.util import await_only

from alembic import op
from fitness_solutions_server.admins.models import Admin
from fitness_solutions_server.admins.utils import send_admin_activation_email
from fitness_solutions_server.core.config import settings
from fitness_solutions_server.core.security import (create_security_token,
                                                    hash_password)

# revision identifiers, used by Alembic.
revision = "7cfee333fb67"
down_revision = "50e1e4c5bd8c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    (raw_activation_token, hashed_activation_token) = create_security_token()
    admin = Admin(
        full_name="Admin User",
        email=settings.ADMIN_EMAIL,
        password_hash=hash_password(str(uuid4())),
        activation_token=hashed_activation_token,
    )
    session = Session(bind=op.get_bind())
    session.add(admin)
    session.commit()

    await_only(
        send_admin_activation_email(email=admin.email, token=raw_activation_token)
    )


def downgrade() -> None:
    pass
