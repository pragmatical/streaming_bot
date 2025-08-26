from __future__ import annotations

from fastapi import FastAPI

from .config.settings import settings
from .controllers.chat_controller import router as chat_router
from .utils.logging import configure_logging


def create_app() -> FastAPI:
    configure_logging(settings.log_level)
    app = FastAPI(title="Streaming Chatbot Demo")
    app.include_router(chat_router)
    return app


app = create_app()
