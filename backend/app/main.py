# Vector Foundry - Main Application Entry Point
"""FastAPI application factory and main entry point."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.database import init_db, close_db
from app.api import issues, auth, llm


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager for startup/shutdown."""
    # Startup
    await init_db()
    yield
    # Shutdown
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