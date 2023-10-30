from fastapi import status

from fitness_solutions_server.core.exceptions import AppException


class OrderCantBeDeclined(AppException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You can't decline an order that is not pending approval",
            code="order_cant_be_declined",
        )


class OrderCantBeApproved(AppException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You can't approve an order that is not pending approval",
            code="order_cant_be_approved",
        )


class OrderCantBeSubmitted(AppException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This order has already been submitted.",
            code="order_cant_be_submitted",
        )


class OrderIncorrectNumberOfWorkouts(AppException):
    def __init__(self, expected: int, actual: int):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"This order requires {expected} workouts, but you have only attached {actual} workouts.",
            code="order_incorrect_number_of_workouts",
        )


class OrderIncorrectNumberOfFitnessPlans(AppException):
    def __init__(self, expected: int, actual: int):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"This order requires {expected} fitness plans, but you have only attached {actual} fitness plans.",
            code="order_incorrect_number_of_fitness_plans",
        )
