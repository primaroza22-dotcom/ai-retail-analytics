"""Application entrypoint for ``uvicorn backend.main:app``."""

from .app import create_app

app = create_app()
