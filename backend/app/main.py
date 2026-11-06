# Vector Foundry - Main Application Entry Point
"""FastAPI application factory and main entry point."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.database import init_db, close_db, get_async_session
from app.api import issues, auth, llm
from app.services.github_sync import GitHubSyncService


scheduler = AsyncIOScheduler()


async def scheduled_sync():
    """Background task to sync issues from GitHub."""
    settings = get_settings()
    if not settings.github_token:
        return  # Skip sync if no GitHub token configured

    async with GitHubSyncService() as sync_service:
        async with get_async_session() as db:
            try:
                await sync_service.sync_all(db, max_pages=5)
            except Exception:
                # Log error but don't crash the scheduler
                pass


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager for startup/shutdown."""
    # Startup
    await init_db()

    # Start background scheduler for periodic sync
    settings = get_settings()
    if settings.github_token and settings.github_sync_interval_minutes > 0:
        scheduler.add_job(
            scheduled_sync,
            "interval",
            minutes=settings.github_sync_interval_minutes,
            id="github_sync",
            replace_existing=True,
        )
        scheduler.start()

    yield

    # Shutdown
    scheduler.shutdown(wait=False)
    await close_db()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Rust compiler feature stabilization tracking and analysis",
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
        openapi_url="/openapi.json" if settings.debug else None,
        lifespan=lifespan,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Health check endpoint (always available)
    @app.get("/health", tags=["health"])
    async def health_check() -> dict[str, str]:
        """Health check endpoint for load balancers and monitoring."""
        return {"status": "healthy", "service": "vector-foundry"}

    @app.get("/health/ready", tags=["health"])
    async def readiness_check() -> dict[str, str]:
        """Readiness check endpoint."""
        return {"status": "ready", "service": "vector-foundry"}

    # API version prefix
    api_prefix = settings.api_prefix

    # Include routers
    app.include_router(issues.router, prefix=api_prefix)
    app.include_router(auth.router, prefix=api_prefix)
    app.include_router(llm.router, prefix=api_prefix)

    return app


# Application instance for uvicorn
app = create_app()


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
