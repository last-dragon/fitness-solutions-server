from uuid import UUID

from fastapi import APIRouter
from sqlalchemy import delete
from sqlalchemy.dialects.postgresql import insert

from fitness_solutions_server.core.database import DatabaseDependency
from fitness_solutions_server.core.schemas import ResponseModel
from fitness_solutions_server.core.utils import get_or_fail
from fitness_solutions_server.fitness_plans.models import FitnessPlan
from fitness_solutions_server.saved_fitness_plans import models
from fitness_solutions_server.users.dependencies import RequireUserDependency

router = APIRouter(prefix="/saved-fitness-plans")


@router.put("/{fitness_plan_id}", summary="Save fitness plan")
async def save_fitness_plan(
    fitness_plan_id: UUID, user: RequireUserDependency, db: DatabaseDependency
) -> ResponseModel[None]:
    fitness_plan = await get_or_fail(FitnessPlan, fitness_plan_id, db)
    insert_stmt = (
        insert(models.user_saved_fitness_plans)
        .values(fitness_plan_id=fitness_plan.id, user_id=user.id)
        .on_conflict_do_nothing()
    )
    await db.execute(insert_stmt)
    await db.commit()
    return ResponseModel(data=None)


@router.delete("/{fitness_plan_id}", summary="Delete saved fitness plan")
async def delete_saved_fitness_plan(
    fitness_plan_id: UUID, user: RequireUserDependency, db: DatabaseDependency
) -> ResponseModel[None]:
    fitness_plan = await get_or_fail(FitnessPlan, fitness_plan_id, db)
    await db.execute(
        delete(models.user_saved_fitness_plans)
        .where(models.user_saved_fitness_plans.c.fitness_plan_id == fitness_plan.id)
        .where(models.user_saved_fitness_plans.c.user_id == user.id)
    )
    await db.commit()
    return ResponseModel(data=None)
