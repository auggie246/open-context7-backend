import secrets
from typing import Annotated

from fastapi import Depends, FastAPI, Header, Request, status
from fastapi.responses import JSONResponse

from app.settings import Settings, get_settings


class UnauthorizedError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message: str = message


async def unauthorized_handler(_: Request, error: Exception) -> JSONResponse:
    match error:
        case UnauthorizedError(message=message):
            error_message = message
        case _:
            error_message = "Unauthorized"
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"error": "unauthorized", "message": error_message},
    )


def register_auth_exception_handler(app: FastAPI) -> None:
    app.add_exception_handler(UnauthorizedError, unauthorized_handler)


def require_bearer_auth(
    settings: Annotated[Settings, Depends(get_settings)],
    authorization: Annotated[str | None, Header()] = None,
) -> None:
    if not settings.api_keys:
        return
    if authorization is None:
        message = "Bearer token required"
        raise UnauthorizedError(message)
    prefix = "Bearer "
    if not authorization.startswith(prefix):
        message = "Bearer token required"
        raise UnauthorizedError(message)
    token = authorization.removeprefix(prefix)
    token_matches = False
    for api_key in settings.api_keys:
        token_matches = secrets.compare_digest(token, api_key) or token_matches
    if not token_matches:
        message = "Invalid bearer token"
        raise UnauthorizedError(message)
