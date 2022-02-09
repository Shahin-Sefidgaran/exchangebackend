from db.pgsql.engine import AsyncDBSession
from convert_service import dependency
from common.resources import response_strings
from common.schemas import ResponseSchema

async def check_currencies(fromcurrency, tocurrency):
    db_async_session = AsyncDBSession()
    response = await dependency.get_list(db_async_session)
    await db_async_session.close()
    list_of_coins = [elem.short_name for elem in response]
    if fromcurrency.upper() and tocurrency.upper() in list_of_coins:
        return True
    return False # checks if the requested currencies exists in the exchange supported currencies.


async def check_market(fromcurrency, tocurrency):
    db_async_session = AsyncDBSession()
    response = await dependency.get_list(db_async_session)
    await db_async_session.close()
    list_of_markets = [value for elem in response for value in elem.markets if elem.markets != ['']]
    if (fromcurrency+tocurrency).upper() in list_of_markets:
        return True
    return False # checks if the requested market exists in the exchange supported markets.


async def make_convert_response(res1 , res2):
    if res1["status"] == "ok" and res2["status"] == "ok":
        convert_response = {
        "status": "ok",
        "data": {
            "id": str(res2["data"]["id"])+','+str(res2["data"]["id"]),
            "create_time": (res1["data"]["create_time"]),
            "finished_time": (res2["data"]["create_time"]),
            "amount": res1["data"]["amount"],
            "deal_amount": res2["data"]["deal_amount"],
            "deal_fee": str(float(res1["data"]["deal_fee"]) + float(res2["data"]["deal_fee"])),
            "money_fee": str(float(res1["data"]["deal_fee"]) + float(res2["data"]["deal_fee"])),
            "avg_price": "",
            "market": (res1["data"]["market"] + res2["data"]["market"]).replace("USDT",""),
            "order_type": "Convert",
            "status": "done",
        },
        "errors": []
        }
        return convert_response
    else:
        return ResponseSchema(data={'msg': response_strings.CONVERT_SECOND_OPERATION_FAILD})
    

