from fastapi import APIRouter, Depends, Request, Response, status
from fastapi.templating import Jinja2Templates

from fitness_solutions_server.admins import schemas
from fitness_solutions_server.admins.dependencies import (
    RequireAdminDependency,
    require_admin_authentication_token,
)
from fitness_solutions_server.admins.exceptions import (
    AdminEmailAlreadyTakenException,
    AdminInvalidActivationTokenException,
    AdminInvalidCredentialsException,
    AdminNotActivatedException,
)
from fitness_solutions_server.admins.service import AdminServiceDependency
from fitness_solutions_server.core.config import settings
from fitness_solutions_server.core.schemas import ResponseModel
from fitness_solutions_server.core.security import (
    security_token_to_code,
    verify_password,
)

router = APIRouter(prefix="/admins")
templates = Jinja2Templates(directory="fitness_solutions_server/templates")


@router.post("", dependencies=[Depends(require_admin_authentication_token)])
async def create_admin(
    admin_create: schemas.AdminCreate, admins: AdminServiceDependency
) -> ResponseModel[schemas.Admin]:
    # Check if email is taken
    if await admins.get_by_email(admin_create.email) is not None:
        raise AdminEmailAlreadyTakenException()

    # Add admin user
    admin = await admins.create(
        full_name=admin_create.full_name, email=admin_create.email
    )

    return ResponseModel(data=schemas.Admin.from_orm(admin))


@router.get("/auth/activate/{token}", include_in_schema=False)
async def serve_activate_page(token: str, request: Request):
    url = f"{settings.BASE_URL}/v1/admins/auth/activate"
    return templates.TemplateResponse(
        "admin_activate.html", {"request": request, "token": token, "url": url}
    )


@router.post("/auth/activate", status_code=status.HTTP_204_NO_CONTENT)
async def activate_admin(
    activation_request: schemas.AdminActivateRequest,
    admins: AdminServiceDependency,
) -> Response:
    # Find admin by token
    admin = await admins.get_by_activation_token(
        security_token_to_code(activation_request.activation_token)
    )
    if admin is None:
        raise AdminInvalidActivationTokenException()

    # Activate account
    await admins.activate(password=activation_request.password, admin=admin)

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/auth/login")
async def login(
    login_request: schemas.AdminLoginRequest, admins: AdminServiceDependency
) -> ResponseModel[schemas.AdminLoginResponse]:
    # Check credentials are correct
    admin = await admins.get_by_email(login_request.email)
    if admin is None:
        raise AdminInvalidCredentialsException()
    if admin.activated_at is None:
        raise AdminNotActivatedException()
    if not verify_password(login_request.password, admin.password_hash):
        raise AdminInvalidCredentialsException()

    # Create authentication token
    unhashed_token = await admins.create_auth_token(admin)

    # Return response
    return ResponseModel(
        data=schemas.AdminLoginResponse(
            token=unhashed_token, admin=schemas.Admin.from_orm(admin)
        )
    )


@router.get("/me")
async def get_current_admin(
    current_admin: RequireAdminDependency,
) -> ResponseModel[schemas.Admin]:
    return ResponseModel(data=schemas.Admin.from_orm(current_admin))
