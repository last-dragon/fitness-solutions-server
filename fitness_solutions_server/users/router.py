from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from pydantic import EmailStr

from fitness_solutions_server.admins.dependencies import IsAdminDependency
from fitness_solutions_server.core.config import settings
from fitness_solutions_server.core.database import DatabaseDependency
from fitness_solutions_server.core.email import (
    send_reset_password_email,
    send_user_verification_email,
)
from fitness_solutions_server.core.schemas import ResponseModel
from fitness_solutions_server.core.security import (
    create_security_token,
    hash_password,
    security_token_to_code,
    verify_password,
)
from fitness_solutions_server.core.utils import get_or_fail
from fitness_solutions_server.countries import models as country_models
from fitness_solutions_server.users.dependencies import (
    GetUserDependency,
    RequireUserDependency,
)
from fitness_solutions_server.users.exceptions import (
    UserEmailAlreadyTakenException,
    UserInvalidCredentialsException,
)
from fitness_solutions_server.weight_logs.models import WeightLog
from fitness_solutions_server.images.models import Image

from . import models, schemas, mapper
from .service import UserServiceDependency

router = APIRouter(prefix="/users")


@router.post("/auth/register", status_code=status.HTTP_201_CREATED)
async def register(
    user_registration: schemas.UserRegistration,
    users: UserServiceDependency,
    db: DatabaseDependency,
    mapper: mapper.UserMapperependency,
) -> ResponseModel[schemas.UserRegistrationResponse]:
    # Check email is not already used
    if await users.get_by_email(user_registration.email) is not None:
        raise UserEmailAlreadyTakenException()

    # Load country
    country = await get_or_fail(
        country_models.Country, user_registration.country_id, db
    )

    # Load Image
    if user_registration.profile_image_id is not None:
        image = await get_or_fail(Image, user_registration.profile_image_id, db)

    # Hash password
    hashed_password = hash_password(user_registration.password)

    # Create user
    del user_registration.password
    del user_registration.confirm_password
    del user_registration.profile_image_id
    (verification_token, verification_code) = create_security_token()
    user = models.User(
        **user_registration.dict(),
        password_hash=hashed_password,
        verification_code=verification_code,
        country=country,
    )
    await users.create(user, profile_image=image)

    # Create initial weight log
    weight_log = WeightLog(user_id=user.id, weight=user_registration.weight)
    db.add(weight_log)

    # TODO: Send verification email in background job
    url = f"{settings.BASE_URL}/v1/users/auth/verify/{verification_token}"  # noqa: E501
    await send_user_verification_email(user.email, url=url)

    # Create authentication token
    unhashed_token = await users.create_auth_token(user=user)

    # Return response
    return ResponseModel(
        data=schemas.UserRegistrationResponse(
            token=unhashed_token, user=mapper.user_to_schema(user)
        )
    )


@router.get("/auth/verify/{token}")
async def verify_email(token: str, users: UserServiceDependency) -> str:
    try:
        verification_code = security_token_to_code(token)
    except Exception:
        return "Invalid verification code"
    user = await users.get_by_verification_code(verification_code)
    if user is None:
        return "Invalid verification code"
    await users.mark_verified(user)
    return "Account verified succesfully."


@router.post("/auth/login")
async def login(
    login_request: schemas.UserLoginRequest,
    users: UserServiceDependency,
    mapper: mapper.UserMapperependency,
) -> ResponseModel[schemas.UserLoginResponse]:
    # Check credentials are correct
    user = await users.get_by_email(login_request.email)
    if user is None or not verify_password(login_request.password, user.password_hash):
        raise UserInvalidCredentialsException()

    # Create authentication token
    unhashed_token = await users.create_auth_token(user=user)

    # Return response
    return ResponseModel(
        data=schemas.UserLoginResponse(
            user=mapper.user_to_schema(user), token=unhashed_token
        )
    )


@router.get("/me")
async def get_current_user(
    current_user: RequireUserDependency, mapper: mapper.UserMapperependency
) -> ResponseModel[schemas.User]:
    return ResponseModel(data=mapper.user_to_schema(current_user))


@router.patch("/{user_id}", summary="Update user")
async def update(
    user_id: UUID,
    update_data: schemas.UserUpdate,
    user: GetUserDependency,
    is_admin: IsAdminDependency,
    db: DatabaseDependency,
    users: UserServiceDependency,
    mapper: mapper.UserMapperependency,
) -> ResponseModel[schemas.User]:
    target_user = await get_or_fail(models.User, user_id, db)

    if (user is not None and user.id != target_user.id) or (
        user is None and not is_admin
    ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    # update_data = body.dict(exclude_unset=True)
    if update_data.profile_image_id is not None:
        image = await get_or_fail(Image, update_data.profile_image_id, db)
        await users.prepare_for_image_update(user=target_user, image=image)
    if update_data.email is not None:
        target_user.email = update_data.email
    if update_data.full_name is not None:
        target_user.full_name = update_data.full_name
    if update_data.sex is not None:
        target_user.sex = update_data.sex
    if update_data.height is not None:
        target_user.height = update_data.height
    if update_data.birthdate is not None:
        target_user.birthdate = update_data.birthdate
    if update_data.focus is not None:
        target_user.focus = update_data.focus
    if update_data.country_id is not None:
        country = await get_or_fail(country_models.Country, update_data.country_id, db)
        target_user.country = country

    await db.commit()
    return ResponseModel(data=mapper.user_to_schema(target_user))


@router.post("/submit_rest_password/{email}")
async def forgot_password(
    email: EmailStr,
    db: DatabaseDependency,
    users: UserServiceDependency,
) -> ResponseModel[schemas.UserResetPassword]:
    user = await users.get_by_email(email)
    (verification_token, verification_code) = create_security_token()
    user.verification_code = verification_code
    await db.commit()
    url = f"{settings.BASE_URL}/v1/users/reset_password/{verification_token}"
    await send_reset_password_email(user.email, url)
    return ResponseModel(
        data=schemas.UserResetPassword(verification_token=verification_token)
    )


@router.post("/reset_password/{token}")
async def reset_password(
    token: str,
    new_password: str,
    users: UserServiceDependency,
    db: DatabaseDependency,
) -> ResponseModel[None]:
    verification_code = security_token_to_code(token)
    user = await users.get_by_verification_code(verification_code)
    hashed_password = hash_password(new_password)
    user.password_hash = hashed_password
    await db.commit()
    return ResponseModel(data=None)


@router.delete("/{user_id}", summary="Delete user")
async def delete(
    user_id: UUID,
    current_user: GetUserDependency,
    is_admin: IsAdminDependency,
    db: DatabaseDependency,
) -> ResponseModel[None]:
    if (current_user is not None and current_user.id != user_id) or (
        current_user is None and not is_admin
    ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    user = await get_or_fail(models.User, user_id, db)
    await db.delete(user)
    await db.commit()

    return ResponseModel(data=None)
