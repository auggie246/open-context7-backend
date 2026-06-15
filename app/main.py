from fastapi import FastAPI

from app.auth import register_auth_exception_handler
from app.models import HealthResponse
from app.routes import router
from app.settings import get_settings


def healthz() -> HealthResponse:
    return HealthResponse(service="open-context7-backend")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Open Context7 Backend",
        debug=False,
    )

    register_auth_exception_handler(app)
    app.include_router(router)
    _ = app.get("/healthz")(healthz)
    app.state.settings = settings
    return app


app = create_app()
