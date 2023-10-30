from fastapi import APIRouter, Depends
from sqlalchemy import select

from fitness_solutions_server.admins.dependencies import (
    require_admin_authentication_token,
)
from fitness_solutions_server.core.database import DatabaseDependency
from fitness_solutions_server.core.schemas import ResponseModel
from fitness_solutions_server.core.utils import get_or_fail

from . import models, schemas

router = APIRouter(prefix="/currencies")


@router.post(
    "",
    summary="Create currency",
    dependencies=[Depends(require_admin_authentication_token)],
)
async def create_currency(
    body: schemas.CurrencyCreate, db: DatabaseDependency
) -> ResponseModel[schemas.Currency]:
    currency = models.Currency(code=body.code, name=body.name)
    db.add(currency)
    await db.commit()
    return ResponseModel(data=schemas.Currency.from_orm(currency))


@router.get(
    "",
    summary="List currencies",
    dependencies=[Depends(require_admin_authentication_token)],
)
async def list_currencies(
    db: DatabaseDependency,
) -> ResponseModel[list[schemas.Currency]]:
    query = select(models.Currency).order_by(models.Currency.code)
    currencies = await db.scalars(query)
    return ResponseModel(data=currencies.all())


@router.delete(
    "/{currency_code}",
    summary="Delete currency",
    dependencies=[Depends(require_admin_authentication_token)],
)
async def delete_currency(
    currency_code: str,
    db: DatabaseDependency,
) -> ResponseModel[None]:
    currency = await get_or_fail(models.Currency, currency_code, db)
    await db.delete(currency)
    await db.commit()
    return ResponseModel(data=None)
