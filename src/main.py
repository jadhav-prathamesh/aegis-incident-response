"""Entry point for running the API server."""

from __future__ import annotations

import uvicorn

from src.core.config import get_settings

settings = get_settings()


def main() -> None:
    """Start the API server with uvicorn."""
    uvicorn.run(
        "src.api.app:app",
        host=settings.host,
        port=settings.port,
        workers=settings.workers,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()
