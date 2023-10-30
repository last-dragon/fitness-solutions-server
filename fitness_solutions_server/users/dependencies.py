from datetime import datetime
from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select

from fitness_solutions_server.core.database import DatabaseDependency
from fitness_solutions_server.core.security import unhashed_token_to_hashed_token
from fitness_solutions_server.users import models
from fitness_solutions_server.users.exceptions import UserUnauthorizedException

security = HTTPBearer(scheme_name="UserToken", auto_error=False)


async def get_user_authentication_token(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
    db: DatabaseDependency,
) -> models.UserAuthenticationToken | None:
    if credentials is None:
        return None

    unhashed_token = credentials.credentials
    hashed_token = unhashed_token_to_hashed_token(unhashed_token)

    auth_token = await db.scalar(
        select(models.UserAuthenticationToken).where(
            models.UserAuthenticationToken.token == hashed_token
        )
    )

    if auth_token is None:
        return None

    if auth_token.expires_at <= datetime.now().astimezone():
        await db.delete(auth_token)
        await db.commit()
        return None

    return auth_token


async def require_user_authentication_token(
    auth_token: Annotated[
        models.UserAuthenticationToken | None, Depends(get_user_authentication_token)
    ],
) -> models.UserAuthenticationToken:
    if auth_token is None:
        raise UserUnauthorizedException()

    return auth_token


async def get_current_user(
    user_authentication_token: Annotated[
        models.UserAuthenticationToken | None, Depends(get_user_authentication_token)
    ],
    db: DatabaseDependency,
) -> models.User | None:
    if user_authentication_token is None:
        return None

    user = await db.get(models.User, user_authentication_token.user_id)

    return user


async def require_current_user(
    user: Annotated[models.User | None, Depends(get_current_user)]
) -> models.User:
    if user is None:
        raise UserUnauthorizedException()

    return user


GetUserDependency = Annotated[models.User | None, Depends(get_current_user)]
RequireUserDependency = Annotated[models.User, Depends(require_current_user)]
