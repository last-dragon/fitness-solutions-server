from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials

from fitness_solutions_server.admins.dependencies import get_admin_authentication_token
from fitness_solutions_server.admins.dependencies import security as admin_security
from fitness_solutions_server.core.database import DatabaseDependency
from fitness_solutions_server.fitness_coaches.dependencies import (
    get_fitness_coach_authentication_token,
)
from fitness_solutions_server.fitness_coaches.dependencies import (
    security as fitness_coach_security,
)
from fitness_solutions_server.users.dependencies import get_user_authentication_token
from fitness_solutions_server.users.dependencies import security as user_security


async def requires_authentication(
    admin_credentials: Annotated[HTTPAuthorizationCredentials, Depends(admin_security)],
    user_credentials: Annotated[HTTPAuthorizationCredentials, Depends(user_security)],
    fitness_coach_credentials: Annotated[
        HTTPAuthorizationCredentials, Depends(fitness_coach_security)
    ],
    db: DatabaseDependency,
):
    # TODO: Worst case we are an admin,
    # and we will have to do extra two database queries.
    # Maybe we can send an additional header to specify what user type we are.
    if (
        await get_user_authentication_token(user_credentials, db) is None
        and await get_fitness_coach_authentication_token(fitness_coach_credentials, db)
        is None
        and await get_admin_authentication_token(admin_credentials, db) is None
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authorized"
        )
