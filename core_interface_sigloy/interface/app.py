import asyncio
import time

from fastapi import APIRouter
from fastapi.responses import ORJSONResponse

from common.resources.response_strings import TIMED_OUT, USER_SAVED
from common.schemas import ResponseSchema
from common.utils import unique_id
from db.pgsql.engine import AsyncDBSession
from db.redis.handler import redis_del_key
from db.redis.namespaces import request_queue_handler_namespace
from interface.crud import create_cex_keys, get_cex_keys, update_cex_keys
from interface.schemas import CexKeysIn, CoreRequestSchema
from request_queue_handler.producer import producer
from request_queue_handler.redis_actions import get_result
from settings import settings

# TODO add handler and security middleware
# TODO disable swagger ui !!

interface_app = APIRouter(
    prefix="/if",
    tags=["Interface"],
    dependencies=[])


@interface_app.post("/handler")
async def interface(core_request: CoreRequestSchema):
    """The main route to the core requests and with a response like:
        {"status":"ok","data":{"status":"ok","data":"pong","errors":[]},"errors":[]}
        the outer "data" keyword is the data returned from this api and the inner "data"
        is the data that is been returned from the "CORE".
    """
    # TODO create dependency to check user_id
    # TODO add encryption here

    req_id = str(unique_id())
    # TODO add logs and gunicorn logs
    await producer({'id': req_id, 'data': core_request.dict()})

    request_time = core_request.req_time
    result = await get_result(request_queue_handler_namespace, req_id)
    while result is None:
        if time.time() - request_time > settings.REQUEST_TIMEOUT:
            return ResponseSchema(status='fail', errors=[{'msg': TIMED_OUT}])
        else:
            await asyncio.sleep(0.1)
            result = await get_result(request_queue_handler_namespace, req_id)
    asyncio.create_task(redis_del_key(request_queue_handler_namespace, req_id))
    return ORJSONResponse(content=result)


@interface_app.post("/store_keys")
async def store_keys(cex_keys: CexKeysIn):
    """checks if user keys exists and new keys are different updates them
    else just return the response."""
    async with AsyncDBSession() as async_session:
        old_cex_keys = await get_cex_keys(async_session, cex_keys.user_id)
        if old_cex_keys:
            if old_cex_keys.access_id == cex_keys.access_id and \
                    old_cex_keys.secret_key == cex_keys.secret_key:
                return ResponseSchema(data={'msg': USER_SAVED})
            else:
                await update_cex_keys(async_session, cex_keys=old_cex_keys, use_orm=False, access_id=cex_keys.access_id,
                                      secret_key=cex_keys.secret_key)
        else:
            await create_cex_keys(async_session, cex_keys.user_id,
                                  cex_keys.access_id, cex_keys.secret_key)
        return ResponseSchema(data={'msg': USER_SAVED})
