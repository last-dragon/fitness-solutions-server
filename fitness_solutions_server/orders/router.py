from typing import Annotated
from unittest import result
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi_pagination import pagination_ctx
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy import func, select

from fitness_solutions_server.admins.dependencies import (
    IsAdminDependency,
    require_admin_authentication_token,
)
from fitness_solutions_server.core.database import DatabaseDependency
from fitness_solutions_server.core.schemas import ResponseModel
from fitness_solutions_server.core.utils import CursorPage, get_or_fail
from fitness_solutions_server.fitness_coaches.dependencies import (
    RequireFitnessCoachDependency,
    get_current_fitness_coach,
)
from fitness_solutions_server.fitness_coaches.models import FitnessCoach
from fitness_solutions_server.fitness_plans.models import (
    FitnessPlan,
    FitnessPlanWeek,
    FitnessPlanWeekWorkout,
)
from fitness_solutions_server.orders import models, schemas
from fitness_solutions_server.orders.exceptions import (
    OrderCantBeApproved,
    OrderCantBeDeclined,
    OrderCantBeSubmitted,
    OrderIncorrectNumberOfFitnessPlans,
    OrderIncorrectNumberOfWorkouts,
)
from fitness_solutions_server.workouts.models import Workout

router = APIRouter(prefix="/orders")


@router.post(
    "",
    summary="Create order",
    dependencies=[Depends(require_admin_authentication_token)],
    status_code=status.HTTP_201_CREATED,
)
async def create(
    create_request: schemas.OrderCreate, db: DatabaseDependency
) -> ResponseModel[schemas.Order]:
    order = models.Order(**create_request.dict())
    db.add(order)
    await db.commit()
    return ResponseModel(data=schemas.Order.from_orm(order))


@router.get("/{order_id}", summary="Get order by ID")
async def get_by_id(
    order_id: UUID,
    fitness_coach: Annotated[FitnessCoach, Depends(get_current_fitness_coach)],
    is_admin: IsAdminDependency,
    db: DatabaseDependency,
) -> ResponseModel[schemas.Order]:
    order = await get_or_fail(models.Order, order_id, db)

    if (fitness_coach and order.fitness_coach_id != fitness_coach.id) or not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this order!",
        )

    return ResponseModel(data=schemas.Order.from_orm(order))


@router.delete(
    "/{order_id}",
    summary="Delete order",
    dependencies=[Depends(require_admin_authentication_token)],
)
async def delete(order_id: UUID, db: DatabaseDependency) -> ResponseModel[None]:
    order = await get_or_fail(models.Order, order_id, db)
    if order.status == models.OrderStatus.approved:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You can't delete approved orders.",
        )
    await db.delete(order)
    await db.commit()
    return ResponseModel(data=None)


@router.patch(
    "/{order_id}",
    summary="Update order",
    dependencies=[Depends(require_admin_authentication_token)],
)
async def update(
    order_id: UUID,
    order_update: schemas.OrderUpdate,
    db: DatabaseDependency,
) -> ResponseModel[schemas.Order]:
    order = await get_or_fail(models.Order, order_id, db)

    if order_update.description is not None:
        order.description = order_update.description

    await db.commit()

    return ResponseModel(data=schemas.Order.from_orm(order))


@router.get(
    "", summary="List orders", dependencies=[Depends(pagination_ctx(CursorPage))]
)
async def list(
    db: DatabaseDependency,
    fitness_coach: Annotated[FitnessCoach, Depends(get_current_fitness_coach)],
    is_admin: IsAdminDependency,
    order_status: Annotated[
        set[models.OrderStatus] | None,
        Query(alias="status", description="Query for any matching statuses"),
    ] = None,
    fitness_coach_id: Annotated[
        UUID | None,
        Query(description="Allows admins to list for specific fitness coaches"),
    ] = None,
) -> ResponseModel[CursorPage[schemas.Order]]:
    """
    Lists orders

    If this endpoint is called as an fitness coach, only orders for them will be shown.
    """

    query = select(models.Order).order_by(
        models.Order.created_at.desc(), models.Order.id
    )

    if fitness_coach:
        query = query.filter(models.Order.fitness_coach_id == fitness_coach.id)
    elif not is_admin:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED)
    else:
        # We are an admin here
        if fitness_coach_id:
            query = query.filter(models.Order.fitness_coach_id == fitness_coach_id)

    if order_status:
        query = query.filter(models.Order.status.in_(order_status))

    orders = await paginate(db, query)

    return ResponseModel(data=orders)


@router.post(
    "/{order_id}/decline",
    summary="Decline order",
    dependencies=[Depends(require_admin_authentication_token)],
)
async def decline_order(
    order_id: UUID, decline_body: schemas.OrderDeclineBody, db: DatabaseDependency
) -> ResponseModel[schemas.Order]:
    order = await get_or_fail(models.Order, order_id, db)

    if order.status != models.OrderStatus.pending_approval:
        raise OrderCantBeDeclined()

    order.decline_reason = decline_body.reason
    order.status = models.OrderStatus.declined
    await db.commit()

    return ResponseModel(data=schemas.Order.from_orm(order))


@router.post(
    "/{order_id}/approve",
    summary="Approve order",
    dependencies=[Depends(require_admin_authentication_token)],
)
async def approve_order(
    order_id: UUID, db: DatabaseDependency
) -> ResponseModel[schemas.Order]:
    order = await get_or_fail(models.Order, order_id, db)

    if order.status != models.OrderStatus.pending_approval:
        raise OrderCantBeApproved()

    order.status = models.OrderStatus.approved
    order.decline_reason = None
    await db.commit()

    return ResponseModel(data=schemas.Order.from_orm(order))


@router.post("/{order_id}/submit", summary="Submit order")
async def submit_order(
    order_id: UUID, fitness_coach: RequireFitnessCoachDependency, db: DatabaseDependency
) -> ResponseModel[schemas.Order]:
    """
    Submits an order for approval, must be in `pending` or `declined` status.
    """
    order = await get_or_fail(models.Order, order_id, db)

    if order.fitness_coach.id != fitness_coach.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    if (
        order.status != models.OrderStatus.in_progress
        and order.status != models.OrderStatus.declined
    ):
        raise OrderCantBeSubmitted()

    # Validate order has required workouts etc
    match order.type:
        case models.OrderType.workout:
            number_of_workouts_attached = (
                await db.scalars(
                    select(func.count())
                    .select_from(Workout)
                    .filter(Workout.order_id == order_id)
                )
            ).one()

            if number_of_workouts_attached != order.amount:
                raise OrderIncorrectNumberOfWorkouts(
                    expected=order.amount, actual=number_of_workouts_attached
                )
        case models.OrderType.fitness_plan:
            fitness_plans = (
                await db.scalars(
                    select(FitnessPlan).filter(FitnessPlan.order_id == order_id)
                )
            ).all()

            if len(fitness_plans) != order.amount:
                raise OrderIncorrectNumberOfFitnessPlans(
                    expected=order.amount, actual=len(fitness_plans)
                )

            # Check that there are equal amount of workouts in each week
            results = (
                await db.execute(
                    select(
                        func.coalesce(func.count(FitnessPlanWeekWorkout.id), 0),
                        FitnessPlan.id,
                    )
                    .select_from(FitnessPlan)
                    .where(FitnessPlan.order_id == order_id)
                    .join(FitnessPlan.weeks)
                    .join(FitnessPlanWeek.workout_associations, isouter=True)
                    .group_by(FitnessPlanWeek.id, FitnessPlan.id)
                )
            ).all()
            if any(
                [
                    count
                    != next(
                        filter(lambda el: el.id == fitness_plan_id, fitness_plans)
                    ).number_of_workouts_per_week
                    for (count, fitness_plan_id) in results
                ]
            ):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="One of your fitness plan does not have the required number of workouts per week",
                )

    order.status = models.OrderStatus.pending_approval
    await db.commit()

    return ResponseModel(data=schemas.Order.from_orm(order))
