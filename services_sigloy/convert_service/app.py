from fastapi import APIRouter, Body, Depends
from authentication import models
from authentication.dependencies.auth import get_current_active_user
from core_router.routes import core_routes
from settings import settings
from convert_service.utils import check_market, check_currencies, make_convert_response
from common.resources import response_strings
from common.schemas import ResponseSchema
from core_router.app import forward


convert_router = APIRouter(
    prefix="/convert",
    tags=["Convert Operations"],
    dependencies=[])


@convert_router.post(core_routes['check_convert_amount']['uri'])
async def check_amount(fromcurrency=Body(...), tocurrency=Body(...), amount=Body(...)):
    amount = float(amount)
    if await check_currencies(fromcurrency, tocurrency):
        if await check_market(fromcurrency, tocurrency):
            args = {'market' : fromcurrency+tocurrency}
            result = await forward('market_ticker', None, args, ORJSONRes=False)
            last = float(result['data']['ticker']['last'])
            price = float(amount) * last
            price = price - (price * (float(settings.CONVERT_FEE)+0.003))
            return ResponseSchema(data={'convert_value': price })
        if await check_market(tocurrency, fromcurrency):
            args = {'market' : tocurrency+fromcurrency}
            result = await forward('market_ticker', None, args, ORJSONRes=False)
            last = float(result['data']['ticker']['last'])
            price = float(amount) / last
            price = price - (price * (float(settings.CONVERT_FEE)+0.003))
            return ResponseSchema(data={'convert_value': price })
        if fromcurrency != tocurrency:
            args1 = {'market' : fromcurrency+"USDT"}
            args2 = {'market' : tocurrency+"USDT"}
            result1 = await forward('market_ticker', None, args1, ORJSONRes=False)
            result2 = await forward('market_ticker', None, args2, ORJSONRes=False)
            last1 = float(result1['data']['ticker']['last'])
            last2 = float(result2['data']['ticker']['last'])
            price = float(amount) * last1 / last2
            price = price - (price * (float(settings.CONVERT_FEE)+0.006))
            return ResponseSchema(data={'convert_value': price })

    return ResponseSchema(data={'msg': response_strings.CONVERT_FAILED})


"""
convert executes the requested market if the exchange service supports the market else it will convert using two MarketOrders.
"""
@convert_router.post(core_routes['convert']['uri'])
async def convert(fromcurrency=Body(...), tocurrency=Body(...), amount=Body(...), 
                       current_user: models.User = Depends(get_current_active_user)):
    amount = float(amount)
    amount = amount - (amount * float(settings.CONVERT_FEE))

    if fromcurrency != tocurrency:    
        if await check_currencies(fromcurrency,tocurrency):    
            if await check_market(fromcurrency,tocurrency):
                args = {'market':fromcurrency+tocurrency ,'type': "SELL", 'amount': amount}
                response = await forward('order_market', current_user.id, args)

            elif await check_market(tocurrency, fromcurrency):
                args = {'market':tocurrency+fromcurrency ,'type': "BUY", 'amount': amount}
                response = await forward('order_market', current_user.id, args)
                
            else:
                args1 = {'market':fromcurrency+"USDT" ,'type': "SELL", 'amount': amount}
                response1 = await forward('order_market', current_user.id, args1, ORJSONRes=False)
                if response1["status"] == "ok":
                    args2 = {'market':tocurrency+"USDT" ,'type': "BUY", 'amount': float(response1["data"]["deal_money"])-float(response1["data"]["deal_fee"])}
                    response2 = await forward('order_market', current_user.id, args2, ORJSONRes=False)
                    return await make_convert_response(response1,response2)
                response = response1
            return response
        else:
            return ResponseSchema(data={'msg': response_strings.CONVERT_FAILED})
    else:
        return ResponseSchema(data={'msg': response_strings.CONVERT_EQUAL_CURRENCY})        