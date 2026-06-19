from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.services import NotFoundError, ValidationError


def error_response(*, status_code: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
            }
        },
    )


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(NotFoundError)
    def not_found_handler(request: Request, exc: NotFoundError) -> JSONResponse:
        return error_response(status_code=404, code="not_found", message=str(exc))

    @app.exception_handler(ValidationError)
    def validation_handler(request: Request, exc: ValidationError) -> JSONResponse:
        return error_response(status_code=400, code="validation_error", message=str(exc))
