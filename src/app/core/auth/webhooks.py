"""Handles webhook verification for Clerk webhooks."""

from typing import Any

from fastapi import HTTPException, Request
from loguru import logger
from svix.webhooks import Webhook, WebhookVerificationError

from app.core.config import get_settings


async def verify_webhook_signature(request: Request) -> dict[str, Any]:
    """Verify Clerk webhook signature using official Svix library."""
    secret = get_settings().clerk_webhook_secret
    if not secret:
        raise HTTPException(status_code=500, detail="Missing webhook secret")

    # Create Svix webhook instance
    wh = Webhook(secret)

    # Get body as string
    body = await request.body()
    payload = body.decode("utf-8")

    # Get headers
    headers = {
        "svix-id": request.headers.get("svix-id", ""),
        "svix-timestamp": request.headers.get("svix-timestamp", ""),
        "svix-signature": request.headers.get("svix-signature", ""),
    }

    try:
        evt = wh.verify(payload, headers)
        return evt
    except WebhookVerificationError as e:
        logger.error(f"Webhook verification failed: {e}")
        raise HTTPException(status_code=401, detail=str(e)) from e
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        raise HTTPException(status_code=400, detail="Error processing webhook") from e
