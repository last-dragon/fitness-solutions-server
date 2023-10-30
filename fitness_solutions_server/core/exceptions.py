from fastapi import HTTPException, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from fitness_solutions_server.core.schemas import ErrorDetail, ErrorResponse


class AppException(HTTPException):
    code: str | None

    def __init__(self, status_code: int, detail: str, code: str | None) -> None:
        self.code = code
        super().__init__(status_code=status_code, detail=detail)


def custom_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    headers = getattr(exc, "headers", None)

    if isinstance(exc, AppException):
        status_code = exc.status_code
        message = exc.detail
        error_detail = ErrorDetail(code=exc.code, detail=None)
    elif isinstance(exc, RequestValidationError):
        status_code = 422
        message = "Validation error"
        error_detail = ErrorDetail(code="validation_error", detail=exc.errors())
    elif isinstance(exc, StarletteHTTPException):
        status_code = exc.status_code
        message = exc.detail
        error_detail = ErrorDetail()
    else:
        status_code = 500
        message = "Internal Server Error"
        error_detail = ErrorDetail()

    return JSONResponse(
        content=jsonable_encoder(ErrorResponse(error=error_detail, message=message)),
        status_code=status_code,
        headers=headers,
    )
