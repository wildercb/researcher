"""FastAPI application factory for Atlas."""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from typing import TYPE_CHECKING

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from apps.api.deps import get_scheduler_instance, get_storage_instance
from apps.api.routes import calibrate, chat, health, items, pipeline, seeds, sources, trends
from packages.core.config import get_settings

if TYPE_CHECKING:
    from collections.abc import AsyncIterator


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Startup
    storage = get_storage_instance()
    await storage.init()
    scheduler = get_scheduler_instance()
    await scheduler.start()
    yield
    # Shutdown
    await scheduler.stop()
    await storage.close()


def create_app() -> FastAPI:
    get_settings()
    app = FastAPI(
        title="Atlas",
        description="Research Intelligence Platform",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://localhost:8765"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routes
    app.include_router(health.router)
    app.include_router(items.router)
    app.include_router(chat.router)
    app.include_router(seeds.router)
    app.include_router(sources.router)
    app.include_router(trends.router)
    app.include_router(pipeline.router)
    app.include_router(calibrate.router)

    # Serve static frontend in production
    static_dir = Path(__file__).parent.parent / "web" / "out"
    if static_dir.exists():
        app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")

    return app


app = create_app()
