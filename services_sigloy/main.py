import asyncio
from os import path

from fastapi import FastAPI
from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse
from slowapi.errors import RateLimitExceeded
from starlette.exceptions import HTTPException
from starlette.staticfiles import StaticFiles
from starlette.websockets import WebSocket

from authentication.apps.auth import auth_router
from authentication.apps.forget import forget_router
from authentication.apps.two_fa import two_fa_router
from authentication.models import Base
from common.schemas import ResponseSchema
from core_router.app import core_router
from currencies.app import currency_router
from convert_service.app import convert_router
from db.pgsql.engine import engine
from error_handlers import (http_error_handler,
                            validation_error_http422_error_handler, custom_rate_limit_exceeded_handler)
from files.app import file_router
from identification.app import profile_router
from logger.loggers import APP_LOGGER
from logger.tasks import write_log
from notification.app import notification_router
from notification.shared import initiate_notification_socket_manager
from rate_limiter import limiter
from settings import settings

app = FastAPI(
    default_response_class=ORJSONResponse)


@app.on_event("startup")
async def startup_event():
    write_log(APP_LOGGER, 'info', 'fastapi startup', 'Worker started!')

    if settings.MIGRATE_ON_START:
        # create tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
    # run notification message checker
    initiate_notification_socket_manager()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO add allowed hosts to .env
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Throttling settings
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, custom_rate_limit_exceeded_handler)

# TODO (PHASE 2) add response schema for 404 error message
app.add_exception_handler(HTTPException, http_error_handler)

app.add_exception_handler(
    RequestValidationError, validation_error_http422_error_handler)

app.include_router(auth_router)
app.include_router(two_fa_router)
app.include_router(forget_router)
app.include_router(profile_router)
app.include_router(file_router)
app.include_router(notification_router)
app.include_router(currency_router)
app.include_router(convert_router)
app.include_router(core_router)

# serves all public files automatically
app.mount("/public", StaticFiles(directory=path.join('storage', 'public')), name="public")


# =================== TEMP ROUTES ================================
@app.get("/")
@limiter.limit('2/minute')
async def root(request: Request):
    # TODO return main static page here
    return {"message": "Hello from sigloy exchange!"}


# route to test connection
@app.get("/ping")
async def register_user():
    return ORJSONResponse(content={'msg': 'pong'})


@app.websocket("/ws/ping/{count}")
async def websocket_endpoint(count: int, websocket: WebSocket):
    await websocket.accept()
    while count:
        await websocket.send_text("pong")
        await asyncio.sleep(1)
        count -= 1


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=False)
