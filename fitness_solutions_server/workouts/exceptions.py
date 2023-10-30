from fastapi import status

from fitness_solutions_server.core.exceptions import AppException


class OrderNotForYou(AppException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail="You can't create workouts for orders that are not for you.",
            code="order_not_for_you",
        )
