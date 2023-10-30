from fastapi import status

from fitness_solutions_server.core.exceptions import AppException


class UserEmailAlreadyTakenException(AppException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already taken",
            code="user_email_already_taken",
        )


class UserInvalidCredentialsException(AppException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            code="user_invalid_credentials",
        )


class UserUnauthorizedException(AppException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
            code="user_unauthorized",
        )
