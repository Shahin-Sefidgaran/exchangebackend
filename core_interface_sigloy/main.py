from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse
from starlette.exceptions import HTTPException

from common.schemas import ResponseSchema
from db.pgsql.engine import engine, Base
from error_handlers import (http_error_handler,
                            validation_error_http422_error_handler)
from interface.app import interface_app
from logger.loggers import APP_LOGGER
from logger.tasks import write_log
from settings import settings

app = FastAPI(
    default_response_class=ORJSONResponse)


@app.on_event("startup")
async def startup_event():
    write_log(APP_LOGGER, 'info', 'fastapi startup', 'Worker started!')

    # create tables

    if settings.MIGRATE_ON_START:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO add allowed hosts to .env
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# TODO add response schema for 404 error message
app.add_exception_handler(HTTPException, http_error_handler)
app.add_exception_handler(
    RequestValidationError, validation_error_http422_error_handler)

app.include_router(interface_app)


# ===================================================

@app.get("/")
async def root():
    # TODO change this route later
    return ResponseSchema(data={'msg': 'hello from sigloy'})


@app.get("/ping")
async def register_user():
    return ORJSONResponse(content={'msg': 'pong'})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
