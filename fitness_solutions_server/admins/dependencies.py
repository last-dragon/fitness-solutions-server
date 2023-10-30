from datetime import datetime
from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select

from fitness_solutions_server.admins import models
from fitness_solutions_server.admins.exceptions import AdminUnauthorizedException
from fitness_solutions_server.core.database import DatabaseDependency
from fitness_solutions_server.core.security import unhashed_token_to_hashed_token

security = HTTPBearer(scheme_name="AdminToken", auto_error=False)


async def get_admin_authentication_token(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
    db: DatabaseDependency,
) -> models.AdminAuthenticationToken | None:
    if credentials is None:
        return None

    unhashed_token = credentials.credentials
    hashed_token = unhashed_token_to_hashed_token(unhashed_token)

    auth_token = await db.scalar(
        select(models.AdminAuthenticationToken).where(
            models.AdminAuthenticationToken.token == hashed_token
        )
    )

    if auth_token is None:
        return None

    if auth_token.expires_at <= datetime.now().astimezone():
        await db.delete(auth_token)
        await db.commit()
        return None

    return auth_token


async def is_admin(
    admin_authentication_token: Annotated[
        models.AdminAuthenticationToken | None, Depends(get_admin_authentication_token)
    ]
) -> bool:
    return admin_authentication_token is not None


async def require_admin_authentication_token(
    admin_authentication_token: Annotated[
        models.AdminAuthenticationToken | None, Depends(get_admin_authentication_token)
    ]
) -> models.AdminAuthenticationToken:
    if admin_authentication_token is None:
        raise AdminUnauthorizedException()

    return admin_authentication_token


async def get_current_admin(
    admin_authentication_token: Annotated[
        models.AdminAuthenticationToken, Depends(get_admin_authentication_token)
    ],
    db: DatabaseDependency,
) -> models.Admin | None:
    if admin_authentication_token is None:
        return None

    admin = await db.get(models.Admin, admin_authentication_token.admin_id)

    return admin


async def require_current_admin(
    admin: Annotated[models.Admin | None, Depends(get_current_admin)]
) -> models.Admin:
    if admin is None:
        raise AdminUnauthorizedException()

    return admin


GetAdminDependency = Annotated[models.Admin | None, Depends(get_current_admin)]
IsAdminDependency = Annotated[bool, Depends(is_admin)]
RequireAdminDependency = Annotated[models.Admin, Depends(require_current_admin)]
