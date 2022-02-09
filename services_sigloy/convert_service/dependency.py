from currencies import models, crud
from typing import List
from db.pgsql.engine import AsyncDBSession
from common.dependencies import get_db_session
from fastapi import Depends


async def get_list(async_session: AsyncDBSession = Depends(get_db_session)) -> List[models.Currency]:
    currencies = await crud.get_currencies(async_session)
    # changing strings to list while returning the result to the client
    for c in currencies:
        c.markets = c.markets.split(',')
        c.networks = c.networks.split(',')
    return currencies