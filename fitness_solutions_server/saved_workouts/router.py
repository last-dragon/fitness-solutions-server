from uuid import UUID

from fastapi import APIRouter
from sqlalchemy import delete
from sqlalchemy.dialects.postgresql import insert

from fitness_solutions_server.core.database import DatabaseDependency
from fitness_solutions_server.core.schemas import ResponseModel
from fitness_solutions_server.core.utils import get_or_fail
from fitness_solutions_server.saved_workouts import models
from fitness_solutions_server.users.dependencies import RequireUserDependency
from fitness_solutions_server.workouts.models import Workout

router = APIRouter(prefix="/saved-workouts")


@router.put("/{workout_id}", summary="Save workout")
async def save_workout(
    workout_id: UUID, user: RequireUserDependency, db: DatabaseDependency
) -> ResponseModel[None]:
    workout = await get_or_fail(Workout, workout_id, db)
    insert_stmt = (
        insert(models.user_saved_workouts)
        .values(workout_id=workout.id, user_id=user.id)
        .on_conflict_do_nothing()
    )
    await db.execute(insert_stmt)
    await db.commit()
    return ResponseModel(data=None)


@router.delete("/{workout_id}", summary="Delete saved workout")
async def delete_saved_workout(
    workout_id: UUID, user: RequireUserDependency, db: DatabaseDependency
) -> ResponseModel[None]:
    workout = await get_or_fail(Workout, workout_id, db)
    await db.execute(
        delete(models.user_saved_workouts)
        .where(models.user_saved_workouts.c.workout_id == workout.id)
        .where(models.user_saved_workouts.c.user_id == user.id)
    )
    await db.commit()
    return ResponseModel(data=None)
