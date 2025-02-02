"""API V1 Router Module.

This module combines all endpoints from different route handlers
into a single router for the v1 API.
"""

from fastapi import APIRouter

from app.api.v1.endpoints import router as endpoints_router

router = APIRouter()
router.include_router(endpoints_router)
