"""FastAPI application factory.

``create_app`` wires the engine, session factory, routers, exception handlers,
and the real-time subsystem (event bus + WebSocket connection manager). The app
is built via a factory (rather than a module-level instance) so tests can inject
an in-memory SQLite database.
"""

from __future__ import annotations

import asyncio
import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import Settings, get_settings
from .database import create_engine_from_url, create_session_factory
from .exceptions import ConflictError, NotFoundError, ValidationError
from .pipeline import PipelineManager
from .realtime import ConnectionManager, Event, EventBus, EventType
from .routers import router

logger = logging.getLogger(__name__)


def configure_logging(level: str) -> None:
    """Configure production-oriented stdout logging (containers handle rotation)."""
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


async def _heartbeat_loop(manager: ConnectionManager, interval: float) -> None:
    while True:
        await asyncio.sleep(interval)
        await manager.broadcast(Event(EventType.HEARTBEAT, time.time()).to_dict())


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    configure_logging(settings.log_level)

    engine = create_engine_from_url(
        settings.database_url,
        pool_size=settings.database_pool_size,
        max_overflow=settings.database_pool_max_overflow,
        pool_timeout=settings.database_pool_timeout,
    )
    session_factory = create_session_factory(engine)

    event_bus = EventBus()
    connection_manager = ConnectionManager()
    event_bus.subscribe(connection_manager.on_event)
    pipeline_manager = PipelineManager(publish=event_bus.publish)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        logger.info("starting up: %s (env=%s)", settings.app_name, settings.app_env)
        bus_task = asyncio.create_task(event_bus.run())
        heartbeat_task = asyncio.create_task(
            _heartbeat_loop(connection_manager, settings.websocket_heartbeat_interval)
        )
        try:
            yield
        finally:
            logger.info("shutting down")
            for task in (bus_task, heartbeat_task):
                task.cancel()
            await asyncio.gather(bus_task, heartbeat_task, return_exceptions=True)
            pipeline_manager.stop_all()
            engine.dispose()
            logger.info("shutdown complete")

    # NOTE: schema is managed by Alembic migrations, NOT create_all. Tables are
    # never created or destroyed automatically on startup.
    app = FastAPI(title=settings.app_name, debug=settings.app_debug, lifespan=lifespan)
    app.state.engine = engine
    app.state.session_factory = session_factory
    app.state.settings = settings
    app.state.event_bus = event_bus
    app.state.connection_manager = connection_manager
    app.state.pipeline_manager = pipeline_manager

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
