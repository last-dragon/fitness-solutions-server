from fastapi import status

from fitness_solutions_server.core.exceptions import AppException


class AdminEmailAlreadyTakenException(AppException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already taken",
            code="admin_email_already_taken",
        )


class AdminInvalidActivationTokenException(AppException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid activation token",
            code="admin_invalid_activation_token",
        )


class AdminInvalidCredentialsException(AppException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            code="admin_invalid_credentials",
        )


class AdminUnauthorizedException(AppException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
            code="admin_unauthorized",
        )


class AdminNotActivatedException(AppException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="You must activate your account",
            code="admin_not_activated",
        )
