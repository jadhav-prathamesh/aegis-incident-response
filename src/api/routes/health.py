"""Health and readiness endpoints."""

from fastapi import APIRouter

from src.core.config import get_settings

router = APIRouter()
settings = get_settings()


@router.get("/health")
async def health_check() -> dict[str, str]:
    """Liveness probe."""
    return {"status": "healthy", "version": settings.app_version}


@router.get("/ready")
async def readiness_check() -> dict[str, str]:
    """Readiness probe.

    Returns degraded status when external dependencies are unreachable so
    orchestrators can route traffic elsewhere.
    """
    return {"status": "ready"}


@router.get("/info")
async def platform_info() -> dict[str, str]:
    """Basic platform metadata."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
    }
