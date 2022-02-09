from typing import Union

from fastapi import Request, status
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.responses import JSONResponse
from pydantic.error_wrappers import ValidationError


async def validation_error_http422_error_handler(_: Request,
                                                 exc: Union[RequestValidationError, ValidationError]) -> JSONResponse:
    return JSONResponse(
        {"status": "fail", "errors": exc.errors()},
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
    )


async def http_error_handler(_: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse({"status": "fail", "errors": [{'msg': exc.detail}]}, status_code=exc.status_code)
