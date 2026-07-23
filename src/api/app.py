"""FastAPI application for the platform."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import agents, approvals, health, incidents, monitoring, validation
from src.core.config import get_settings
from src.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle."""
    logger.info("Starting API", version=settings.app_version)
    yield
    logger.info("Shutting down API")


def create_app() -> FastAPI:
    """Build and configure the FastAPI application."""
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.security.cors_origins,
        allow_credentials=settings.security.cors_allow_credentials,
        allow_methods=settings.security.cors_allow_methods,
        allow_headers=settings.security.cors_allow_headers,
    )

    # Register routers
    prefix = settings.api_prefix
    app.include_router(health.router, tags=["health"])
    app.include_router(incidents.router, prefix=f"{prefix}/incidents", tags=["incidents"])
    app.include_router(agents.router, prefix=f"{prefix}/agents", tags=["agents"])
    app.include_router(approvals.router, prefix=f"{prefix}/approvals", tags=["approvals"])
    app.include_router(monitoring.router, prefix=f"{prefix}/monitoring", tags=["monitoring"])
    app.include_router(validation.router, prefix=f"{prefix}/validation", tags=["validation"])

    return app


app = create_app()
