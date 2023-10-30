from datetime import datetime
from hmac import new

from fastapi import APIRouter

from fitness_solutions_server.core.database import DatabaseDependency
from fitness_solutions_server.core.schemas import ResponseModel
from fitness_solutions_server.core.utils import get_or_fail
from fitness_solutions_server.user_workouts import schemas
from fitness_solutions_server.users.dependencies import RequireUserDependency
from fitness_solutions_server.workouts.models import Workout

from . import models, schemas, utils

router = APIRouter(prefix="/user-workouts")


@router.post("", summary="Add completed workout")
async def complete_workout(
    body: schemas.UserWorkoutCreate,
    user: RequireUserDependency,
    db: DatabaseDependency,
) -> ResponseModel[schemas.UserWorkout]:
    userworkoutservice = utils.UserWorkoutService(db)
    completed_workout = await userworkoutservice.get_user_workouts_by_workouts_id(
        body.workout_id
    )
    if completed_workout is not None:
        completed_workout.completed_at = datetime.utcnow()

        user.tracked_workouts.append(completed_workout)
        await db.commit()
        return ResponseModel(data=schemas.UserWorkout.from_orm(completed_workout))
    else:
        workouts = await get_or_fail(Workout, body.workout_id, db)
        user_workout = models.UserWorkout(
            workout_id=workouts.workout_id,
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
        )
        user.tracked_workouts.append(user_workout)
        await db.commit()
        return ResponseModel(data=schemas.UserWorkout.from_orm(user_workout))
