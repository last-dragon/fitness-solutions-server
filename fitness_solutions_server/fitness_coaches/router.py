from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from fastapi.templating import Jinja2Templates
from fastapi_pagination import pagination_ctx
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy import func, select, true, update

from fitness_solutions_server.admins.dependencies import (
    IsAdminDependency,
    require_admin_authentication_token,
)
from fitness_solutions_server.collections.models import CollectionItemFitnessCoach
from fitness_solutions_server.core.config import settings
from fitness_solutions_server.core.database import DatabaseDependency
from fitness_solutions_server.core.schemas import ResponseModel
from fitness_solutions_server.core.security import (
    security_token_to_code,
    verify_password,
)
from fitness_solutions_server.core.utils import (
    CursorPage,
    get_or_fail,
    get_or_fail_many,
)
from fitness_solutions_server.countries.models import Country
from fitness_solutions_server.fitness_coaches import models, schemas
from fitness_solutions_server.fitness_coaches.dependencies import (
    GetFitnessCoachDependency,
    RequireFitnessCoachDependency,
)
from fitness_solutions_server.fitness_coaches.exceptions import (
    FitnessCoachEmailAlreadyTakenException,
    FitnessCoachInvalidActivationTokenException,
    FitnessCoachInvalidCredentialsException,
    FitnessCoachNotActivatedException,
)
from fitness_solutions_server.fitness_coaches.mapper import FitnessCoachMapperDependency
from fitness_solutions_server.fitness_coaches.service import (
    FitnessCoachServiceDependency,
)
from fitness_solutions_server.images.models import Image
from fitness_solutions_server.users.dependencies import GetUserDependency
from fitness_solutions_server.workouts.models import Workout

router = APIRouter(prefix="/fitness-coaches")
templates = Jinja2Templates(directory="fitness_solutions_server/templates")


@router.post(
    "",
    dependencies=[Depends(require_admin_authentication_token)],
    status_code=status.HTTP_201_CREATED,
)
async def create_fitness_coach(
    fitness_coach_create: schemas.FitnessCoachCreate,
    fitness_coaches: FitnessCoachServiceDependency,
    db: DatabaseDependency,
    mapper: FitnessCoachMapperDependency,
) -> ResponseModel[schemas.FitnessCoach]:
    # Check if email is taken
    if await fitness_coaches.get_by_email(fitness_coach_create.email) is not None:
        raise FitnessCoachEmailAlreadyTakenException()

    # Load countries
    countries = await get_or_fail_many(Country, fitness_coach_create.countries, db)

    # Load image
    # TODO: Maybe we need FOR UPDATE here, since we move it.
    image = await get_or_fail(Image, fitness_coach_create.profile_image_id, db)

    # Add fitness coach
    del fitness_coach_create.countries
    del fitness_coach_create.profile_image_id
    fitness_coach = models.FitnessCoach(
        **fitness_coach_create.dict(),
        countries=countries,
        number_of_workouts=0,
        number_of_fitness_plans=0,
    )
    fitness_coach = await fitness_coaches.create(fitness_coach, profile_image=image)

    return ResponseModel(data=mapper.fitness_coach_to_schema(fitness_coach))


@router.get("/auth/activate/{token}", include_in_schema=False)
async def serve_activate_page(token: str, request: Request):
    url = f"{settings.BASE_URL}/v1/fitness-coaches/auth/activate"
    return templates.TemplateResponse(
        "fitness_coach_activate.html", {"request": request, "token": token, "url": url}
    )


@router.post("/auth/activate", status_code=status.HTTP_204_NO_CONTENT)
async def activate_fitness_coach(
    activation_request: schemas.FitnessCoachActivateRequest,
    fitness_coaches: FitnessCoachServiceDependency,
) -> Response:
    # Find coach by token
    fitness_coach = await fitness_coaches.get_by_activation_token(
        security_token_to_code(activation_request.activation_token)
    )
    if fitness_coach is None:
        raise FitnessCoachInvalidActivationTokenException()

    # Activate account
    await fitness_coaches.activate(
        password=activation_request.password, fitness_coach=fitness_coach
    )

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/auth/login")
async def login(
    login_request: schemas.FitnessCoachLoginRequest,
    fitness_coaches: FitnessCoachServiceDependency,
    mapper: FitnessCoachMapperDependency,
) -> ResponseModel[schemas.FitnessCoachLoginResponse]:
    # Check credentials are correct
    fitness_coach = await fitness_coaches.get_by_email(login_request.email)
    if fitness_coach is None:
        raise FitnessCoachInvalidCredentialsException()
    if fitness_coach.activated_at is None:
        raise FitnessCoachNotActivatedException()
    if not verify_password(login_request.password, fitness_coach.password_hash):
        raise FitnessCoachInvalidCredentialsException()

    # Create authentication token
    unhashed_token = await fitness_coaches.create_auth_token(fitness_coach)

    # Return response
    return ResponseModel(
        data=schemas.FitnessCoachLoginResponse(
            token=unhashed_token,
            fitness_coach=mapper.fitness_coach_to_schema(fitness_coach),
        )
    )


@router.get("/me")
async def me(
    current_fitness_coach: RequireFitnessCoachDependency,
    mapper: FitnessCoachMapperDependency,
) -> ResponseModel[schemas.FitnessCoach]:
    return ResponseModel(data=mapper.fitness_coach_to_schema(current_fitness_coach))


@router.get("/{fitness_coach_id}", summary="Get fitness coach by ID")
async def get_by_id(
    fitness_coach_id: UUID, db: DatabaseDependency, mapper: FitnessCoachMapperDependency
) -> ResponseModel[schemas.FitnessCoach]:
    fitness_coach = await get_or_fail(models.FitnessCoach, fitness_coach_id, db)
    return ResponseModel(data=mapper.fitness_coach_to_schema(fitness_coach))


@router.get(
    "",
    summary="List fitness coaches",
    dependencies=[Depends(pagination_ctx(CursorPage))],
)
async def list(
    user: GetUserDependency,
    mapper: FitnessCoachMapperDependency,
    db: DatabaseDependency,
    is_admin: IsAdminDependency,
    name: Annotated[str | None, Query(description="Search for names")] = None,
    country_id: Annotated[
        UUID | None,
        Query(
            description="Used to list coaches for a specific country, if not specified user country will be used"
        ),
    ] = None,
    collection_id: Annotated[UUID | None, Query()] = None,
) -> ResponseModel[CursorPage[schemas.FitnessCoach]]:
    query = select(models.FitnessCoach).order_by(
        models.FitnessCoach.full_name, models.FitnessCoach.id
    )

    if country_id is not None:
        query = query.filter(models.FitnessCoach.countries.any(id=country_id))
    elif user is not None:
        query = query.filter(models.FitnessCoach.countries.any(id=user.country_id))

    if name is not None:
        query = query.where(models.FitnessCoach.full_name.ilike(f"%{name}%"))

    if collection_id is not None:
        exists_stmt = (
            select(CollectionItemFitnessCoach.id)
            .where(
                CollectionItemFitnessCoach.fitness_coach_id == models.FitnessCoach.id
            )
            .exists()
        )
        query = query.where(
            exists_stmt.where(CollectionItemFitnessCoach.collection_id == collection_id)
        )
    else:
        if not is_admin:
            query = query.where(models.FitnessCoach.is_released == true())

    fitness_coaches = await paginate(
        db, query, transformer=mapper.fitness_coaches_to_schema
    )

    return ResponseModel(data=fitness_coaches)


@router.patch("/{fitness_coach_id}", summary="Update fitness coach")
async def update_fitness_coach(
    fitness_coach_id: UUID,
    update_request: schemas.FitnessCoachUpdate,
    db: DatabaseDependency,
    fitness_coach: GetFitnessCoachDependency,
    is_admin: IsAdminDependency,
    mapper: FitnessCoachMapperDependency,
    fitness_coaches: FitnessCoachServiceDependency,
) -> ResponseModel[schemas.FitnessCoach]:
    target_fitness_coach = await get_or_fail(models.FitnessCoach, fitness_coach_id, db)

    if (fitness_coach is not None and fitness_coach.id != target_fitness_coach.id) or (
        fitness_coach is None and not is_admin
    ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    if update_request.profile_image_id is not None:
        image = await get_or_fail(Image, update_request.profile_image_id, db)
        await fitness_coaches.prepare_for_image_update(
            fitness_coach=target_fitness_coach, image=image
        )
    if update_request.email is not None:
        target_fitness_coach.email = update_request.email
    if update_request.full_name is not None:
        target_fitness_coach.full_name = update_request.full_name
    if update_request.title is not None:
        target_fitness_coach.title = update_request.title
    if update_request.description is not None:
        target_fitness_coach.description = update_request.description
    if update_request.sex is not None:
        target_fitness_coach.sex = update_request.sex
    if update_request.is_released is not None and is_admin:
        target_fitness_coach.is_released = update_request.is_released

    await db.commit()

    return ResponseModel(data=mapper.fitness_coach_to_schema(target_fitness_coach))


@router.delete("/{fitness_coach_id}", summary="Delete fitness coach")
async def delete(
    fitness_coach_id: UUID,
    db: DatabaseDependency,
    fitness_coach: GetFitnessCoachDependency,
    is_admin: IsAdminDependency,
) -> ResponseModel[None]:
    target_fitness_coach = await get_or_fail(models.FitnessCoach, fitness_coach_id, db)

    if (fitness_coach is not None and fitness_coach.id != target_fitness_coach.id) or (
        fitness_coach is None and not is_admin
    ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    # Mark workouts as deleted
    await db.execute(
        update(Workout)
        .where(Workout.fitness_coach_id == target_fitness_coach.id)
        .where(Workout.deleted_at.is_(None))
        .values(deleted_at=func.now(), fitness_coach_id=None)
    )

    # Delete fitness coach from database
    await db.delete(target_fitness_coach)

    await db.commit()

    return ResponseModel(data=None)
