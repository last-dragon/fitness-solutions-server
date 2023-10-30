from datetime import datetime
from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select

from fitness_solutions_server.core.database import DatabaseDependency
from fitness_solutions_server.core.security import unhashed_token_to_hashed_token
from fitness_solutions_server.fitness_coaches import models
from fitness_solutions_server.fitness_coaches.exceptions import (
    FitnessCoachUnauthorizedException,
)

security = HTTPBearer(scheme_name="FitnessCoachToken", auto_error=False)


async def get_fitness_coach_authentication_token(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
    db: DatabaseDependency,
) -> models.FitnessCoachAuthenticationToken | None:
    if credentials is None:
        return None

    unhashed_token = credentials.credentials
    hashed_token = unhashed_token_to_hashed_token(unhashed_token)

    auth_token = await db.scalar(
        select(models.FitnessCoachAuthenticationToken).where(
            models.FitnessCoachAuthenticationToken.token == hashed_token
        )
    )

    if auth_token is None:
        return None

    if auth_token.expires_at <= datetime.now().astimezone():
        await db.delete(auth_token)
        await db.commit()
        return None

    return auth_token


async def require_fitness_coach_authentication_token(
    auth_token: Annotated[
        models.FitnessCoachAuthenticationToken,
        Depends(get_fitness_coach_authentication_token),
    ],
) -> models.FitnessCoachAuthenticationToken:
    if auth_token is None:
        raise FitnessCoachUnauthorizedException()

    return auth_token


async def is_fitness_coach(
    auth_token: Annotated[
        models.FitnessCoachAuthenticationToken | None,
        Depends(get_fitness_coach_authentication_token),
    ]
) -> bool:
    return auth_token is not None


async def get_current_fitness_coach(
    authentication_token: Annotated[
        models.FitnessCoachAuthenticationToken | None,
        Depends(get_fitness_coach_authentication_token),
    ],
    db: DatabaseDependency,
) -> models.FitnessCoach | None:
    if authentication_token is None:
        return None

    fitness_coach = await db.get(
        models.FitnessCoach, authentication_token.fitness_coach_id
    )

    return fitness_coach


async def require_current_fitness_coach(
    fitness_coach: Annotated[
        models.FitnessCoach | None,
        Depends(get_current_fitness_coach),
    ],
) -> models.FitnessCoach:
    if fitness_coach is None:
        raise FitnessCoachUnauthorizedException()

    return fitness_coach


IsFitnessCoachDependency = Annotated[bool, Depends(is_fitness_coach)]
GetFitnessCoachDependency = Annotated[
    models.FitnessCoach | None, Depends(get_current_fitness_coach)
]

RequireFitnessCoachDependency = Annotated[
    models.FitnessCoach, Depends(require_current_fitness_coach)
]
