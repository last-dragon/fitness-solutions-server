from fastapi import status

from fitness_solutions_server.core.exceptions import AppException


class FitnessCoachEmailAlreadyTakenException(AppException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already taken",
            code="fitness_coach_email_already_taken",
        )


class FitnessCoachInvalidActivationTokenException(AppException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid activation token",
            code="fitness_coach_invalid_activation_token",
        )


class FitnessCoachInvalidCredentialsException(AppException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            code="fitness_coach_invalid_credentials",
        )


class FitnessCoachUnauthorizedException(AppException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
            code="fitness_coach_unauthorized",
        )


class FitnessCoachNotActivatedException(AppException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="You must activate your account",
            code="fitness_coach_not_activated",
        )
