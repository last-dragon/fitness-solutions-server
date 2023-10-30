from datetime import datetime
from typing import Annotated
from uuid import uuid4

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fitness_solutions_server.admins import models
from fitness_solutions_server.admins.utils import send_admin_activation_email
from fitness_solutions_server.core.config import settings
from fitness_solutions_server.core.database import DatabaseDependency
from fitness_solutions_server.core.security import (
    create_security_token,
    generate_authentication_token,
    hash_password,
)


class AdminService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_email(self, email: str) -> models.Admin | None:
        return await self.db.scalar(
            select(models.Admin).where(models.Admin.email == email)
        )

    async def get_by_activation_token(self, token: str) -> models.Admin | None:
        return await self.db.scalar(
            select(models.Admin).where(models.Admin.activation_token == token)
        )

    async def create(self, full_name: str, email: str) -> models.Admin:
        (raw_activation_code, hashed_activation_code) = create_security_token()
        admin = models.Admin(
            full_name=full_name,
            email=email,
            password_hash=hash_password(str(uuid4())),
            activation_token=hashed_activation_code,
        )
        self.db.add(admin)
        await self.db.commit()
        await send_admin_activation_email(email=admin.email, token=raw_activation_code)
        return admin

    async def activate(self, password: str, admin: models.Admin):
        admin.password_hash = hash_password(password)
        admin.activated_at = datetime.utcnow()
        admin.activation_token = None
        await self.db.commit()

    async def create_auth_token(self, admin: models.Admin) -> str:
        (unhashed_token, hashed_token) = generate_authentication_token()
        auth_token_model = models.AdminAuthenticationToken(
            token=hashed_token,
            admin_id=admin.id,
            expires_at=datetime.now().astimezone() + settings.ADMIN_AUTH_EXPIRE_DELTA,
        )
        self.db.add(auth_token_model)
        await self.db.commit()
        return unhashed_token


def get_admin_service(db: DatabaseDependency) -> AdminService:
    return AdminService(db=db)


AdminServiceDependency = Annotated[AdminService, Depends(get_admin_service)]
