import logging

from fastapi import APIRouter, Depends, FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi_pagination import add_pagination
from starlette.exceptions import HTTPException as StarletteHTTPException

from fitness_solutions_server.core.config import settings
from fitness_solutions_server.core.exceptions import (
    AppException,
    custom_exception_handler,
)
from fitness_solutions_server.core.localization import accept_language_dependency

from .admins import router as admins_router
from .collections import router as collections_router
from .countries import router as countries_router
from .currencies import router as currencies_router
from .equipment import router as equipment_router
from .exercises import router as exercises_router
from .fitness_coaches import router as fitness_coaches_router
from .fitness_plans import participations_router
from .fitness_plans import router as fitness_plans_router
from .images import router as images_router
from .muscle_groups import router as muscles_groups_router
from .orders import router as orders_router
from .pr_observations import router as pr_observations_router
from .products import router as products_router
from .saved_fitness_plans import router as saved_fitness_plans_router
from .saved_workouts import router as saved_workouts_router
from .user_workouts import router as user_workouts_router
from .users import router as users_router
from .weight_logs import router as weight_logs_router
from .workouts import router as workouts_router

logging.basicConfig(
    encoding="utf-8",
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

app = FastAPI(dependencies=[Depends(accept_language_dependency)])
add_pagination(app)
app.add_exception_handler(AppException, custom_exception_handler)
app.add_exception_handler(RequestValidationError, custom_exception_handler)
app.add_exception_handler(StarletteHTTPException, custom_exception_handler)
app.add_exception_handler(Exception, custom_exception_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.BASE_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

v1 = APIRouter(prefix="/v1")
v1.include_router(users_router.router, tags=["Users"])
v1.include_router(admins_router.router, tags=["Admins"])
v1.include_router(fitness_coaches_router.router, tags=["Fitness Coaches"])
v1.include_router(countries_router.router, tags=["Countries"])
v1.include_router(images_router.router, tags=["Images"])
v1.include_router(equipment_router.router, tags=["Equipment"])
v1.include_router(muscles_groups_router.router, tags=["Muscle Groups"])
v1.include_router(exercises_router.router, tags=["Exercises"])
v1.include_router(orders_router.router, tags=["Orders"])
v1.include_router(workouts_router.router, tags=["Workouts"])
v1.include_router(saved_workouts_router.router, tags=["Saved Workouts"])
v1.include_router(user_workouts_router.router, tags=["Completed Workouts"])
v1.include_router(weight_logs_router.router, tags=["Weight Logs"])
v1.include_router(fitness_plans_router.router, tags=["Fitness Plans"])
v1.include_router(participations_router.router, tags=["Fitness Plans"])
v1.include_router(saved_fitness_plans_router.router, tags=["Saved Fitness Plans"])
v1.include_router(pr_observations_router.router, tags=["PR Observations"])
v1.include_router(collections_router.router, tags=["Collections"])
v1.include_router(products_router.router, tags=["Products"])
v1.include_router(currencies_router.router, tags=["Currencies"])

app.include_router(v1)
