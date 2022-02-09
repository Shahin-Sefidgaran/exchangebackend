from typing import Union

from fastapi import Request, status
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.responses import JSONResponse, ORJSONResponse
from pydantic.error_wrappers import ValidationError
from slowapi.errors import RateLimitExceeded
from starlette.responses import Response


async def validation_error_http422_error_handler(
        _: Request,
        exc: Union[RequestValidationError, ValidationError],
) -> JSONResponse:
    return ORJSONResponse(
        {"status": "fail", "errors": exc.errors()},
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
    )


async def http_error_handler(_: Request, exc: HTTPException) -> ORJSONResponse:
    return ORJSONResponse({"status": "fail", "errors": [{'msg': exc.detail}]}, status_code=exc.status_code)


def custom_rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> Response:
    """
    Build a simple JSON response that includes the details of the rate limit
    that was hit. If no limit is hit, the countdown is added to headers.
    """
    detail = exc.detail  # can be used for later(info about limit counts)
    response = ORJSONResponse(
        {"status": "fail", "errors": [{'msg': "Rate limit exceeded"}]}, status_code=429,
    )
    response = request.app.state.limiter._inject_headers(
        response, request.state.view_rate_limit
    )
    return response
