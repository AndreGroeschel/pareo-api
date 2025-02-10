"""User Management Endpoints.

This module handles Clerk webhook endpoints for user lifecycle management,
including user creation, updates, and deletion through webhook events.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from loguru import logger

from app.api.dependencies import get_clerk_sync_service
from app.core.auth.webhooks import verify_webhook_signature
from app.core.exceptions import UserOperationError
from app.models.user import ClerkWebhookEvent, WebhookResponse
from app.services.clerk_user_sync_service import ClerkUserSyncService

router = APIRouter()


@router.post(
    "/clerk-webhooks",
    response_model=WebhookResponse,
    status_code=status.HTTP_200_OK,
    tags=["auth"],
    include_in_schema=False,
)
async def handle_clerk_webhooks(
    request: Request,
    clerk_user_sync_service: Annotated[ClerkUserSyncService, Depends(get_clerk_sync_service)],
) -> WebhookResponse:
    """Handle Clerk user sync webhooks.

    Processes webhook events from Clerk for user lifecycle management:
    - user.created: Creates new user record
    - user.updated: Updates existing user information
    - user.deleted: Soft deletes user record

    Args:
        request: The incoming webhook request
        clerk_user_sync_service: Instance of ClerkUserSyncService for managing user synchronization.

    Returns:
        WebhookResponse indicating the operation status

    Raises:
        HTTPException: For invalid signatures or processing errors

    """
    logger.info("Processing Clerk webhook")

    # Verify webhook signature
    await verify_webhook_signature(request)
    payload = await request.json()

    try:
        webhook_data = ClerkWebhookEvent(**payload)
        logger.info(f"Processing Clerk webhook: {webhook_data.type}")
        if webhook_data.type == "user.created":
            user_id = await clerk_user_sync_service.sync_new_user(webhook_data)
            return WebhookResponse(status="created", user_id=str(user_id))

        elif webhook_data.type == "user.updated":
            await clerk_user_sync_service.sync_update_user(webhook_data)
            return WebhookResponse(status="updated")

        elif webhook_data.type == "user.deleted":
            await clerk_user_sync_service.sync_delete_user(webhook_data.data.id)
            return WebhookResponse(status="deleted")

        else:
            logger.warning(f"Unhandled webhook event type: {webhook_data.type}")
            return WebhookResponse(status="ignored")

    except UserOperationError as e:
        logger.error(f"User operation failed: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e

    except Exception as e:
        logger.error(f"Webhook processing failed: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error") from e
