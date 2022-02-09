from typing import List
from fastapi import APIRouter, Depends, HTTPException
from starlette import status

from common.resources import response_strings
from common.schemas import ResponseSchema
from currencies import crud
from db.pgsql.engine import AsyncDBSession
from common.dependencies import get_db_session
from currencies.schemas import CurrencySchema
from settings import settings

currency_router = APIRouter(
    prefix="/currencies",
    tags=["Currency information"],
    dependencies=[])


@currency_router.get("/list", response_model=List[CurrencySchema])
async def get_list(async_session: AsyncDBSession = Depends(get_db_session)):
    currencies = await crud.get_currencies(async_session)
    # changing strings to list while returning the result to the client
    for c in currencies:
        c.markets = c.markets.split(',')
        c.networks = c.networks.split(',')
    return currencies


if settings.DEBUG:
    """
    CRUD functions of editing the currencies that the exchange servise supports.
    should only be accessible to admins later in the admin panel.
    """
    
    @currency_router.post("/add")
    async def create_currency(new_currency: CurrencySchema, async_session: AsyncDBSession = Depends(get_db_session)):
        # converting array to string separated by commas
        new_currency.markets = ','.join(new_currency.markets)
        new_currency.networks = ','.join(new_currency.networks)
        await crud.create_currency(async_session, short_name=new_currency.short_name, full_name=new_currency.full_name,
                                   networks=new_currency.networks, markets=new_currency.markets, rank=new_currency.rank, is_stable=new_currency.is_stable)
        return ResponseSchema(data={'msg': response_strings.CURRENCY_ADDED_SUCCESS})


    @currency_router.put("/update")
    async def update_coin(updated_currency: CurrencySchema,
                          async_session: AsyncDBSession = Depends(get_db_session)):
        # converting array to string separated by commas
        updated_currency.markets = ','.join(updated_currency.markets)
        updated_currency.networks = ','.join(updated_currency.networks)
        currency = await crud.get_currency(async_session, updated_currency.short_name)
        if currency:
            await crud.update_currency(async_session, currency, use_orm=True,
                                       **updated_currency.dict())
            return ResponseSchema(data={'msg': response_strings.CURRENCY_UPDATED_SUCCESS})
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=response_strings.NOT_FOUND,
        )


    @currency_router.delete("/delete/{currency_short_name}")
    async def delete_coin(currency_short_name: str, async_session: AsyncDBSession = Depends(get_db_session)):
        currency = await crud.get_currency(async_session, currency_short_name)
        if currency:
            await crud.delete_currency(async_session, currency)
            return ResponseSchema(data={'msg': response_strings.CURRENCY_DELETED_SUCCESS})
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=response_strings.NOT_FOUND,
        )
