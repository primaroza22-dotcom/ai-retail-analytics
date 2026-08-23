"""FastAPI application factory.

``create_app`` wires the engine, session factory, routers, and exception
handlers. The app is built via a factory (rather than a module-level instance)
so tests can inject an in-memory SQLite database.
"""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import Settings, get_settings
from .database import create_engine_from_url, create_session_factory
from .exceptions import ConflictError, NotFoundError, ValidationError
from .routers import router


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()

    engine = create_engine_from_url(settings.database_url)
    session_factory = create_session_factory(engine)

    # NOTE: schema is managed by Alembic migrations, NOT create_all. Tables are
    # never created or destroyed automatically on startup.
    app = FastAPI(title=settings.app_name, debug=settings.app_debug)
    app.state.engine = engine
    app.state.session_factory = session_factory
    app.state.settings = settings

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(router)
    _register_exception_handlers(app)
    return app


def _register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(NotFoundError)
    async def not_found(request: Request, exc: NotFoundError) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(ConflictError)
    async def conflict(request: Request, exc: ConflictError) -> JSONResponse:
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    @app.exception_handler(ValidationError)
    async def validation(request: Request, exc: ValidationError) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": str(exc)})
