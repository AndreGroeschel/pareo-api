"""Main Application Module.

This module initializes the FastAPI application and configures global settings,
middleware, and routers. It serves as the entry point for the application.
"""

from fastapi import FastAPI

from app.api.v1.router import router as v1_router
from app.core.config import settings

app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    debug=settings.debug,
    description="""
    A minimal FastAPI application with proper documentation and structure.
    This API demonstrates best practices for building scalable FastAPI applications.
    """,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.include_router(v1_router, prefix="/api/v1")


@app.get("/health", tags=["system"])
async def health_check() -> dict[str, str]:
    """Perform a health check of the application.

    Returns:
        dict: A dictionary containing the health status of the application.

    Example:
        Response:
        ```json
        {
            "status": "healthy"
        }
        ```

    """
    return {"status": "healthy"}
