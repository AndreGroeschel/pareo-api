"""API V1 Router Module.

This module combines all endpoints from different route handlers
into a single router for the v1 API.
"""

from fastapi import APIRouter

from app.api.v1.billing_endpoints import router as billing_router
from app.api.v1.clerk_user_sync_endpoints import router as clerk_user_sync_router
from app.api.v1.credit_endpoints import router as credit_router
from app.api.v1.investor_endpoints import router as investors_router
from app.api.v1.payment_endpoints import router as payment_router

router = APIRouter()
router.include_router(investors_router, prefix="/investors")
router.include_router(clerk_user_sync_router, prefix="/clerk-sync")
router.include_router(credit_router, prefix="/credits", tags=["credits"])
router.include_router(payment_router, prefix="/payments", tags=["payments"])
router.include_router(billing_router)
