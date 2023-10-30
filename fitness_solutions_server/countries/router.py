from fastapi import APIRouter
from sqlalchemy import select

from fitness_solutions_server.core.database import DatabaseDependency
from fitness_solutions_server.core.schemas import ResponseModel
from fitness_solutions_server.countries import models, schemas

router = APIRouter(prefix="/countries")


@router.get("")
async def get_countries(db: DatabaseDependency) -> ResponseModel[list[schemas.Country]]:
    countries = await db.scalars(select(models.Country).order_by(models.Country.name))
    return ResponseModel(data=[schemas.Country.from_orm(c) for c in countries.all()])
