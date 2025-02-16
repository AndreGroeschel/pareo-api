"""Payment-related API endpoints."""

from typing import Annotated, cast

import stripe
from fastapi import APIRouter, Depends, HTTPException, Request, status
from loguru import logger

from app.api.dependencies import get_payment_service
from app.core.auth.auth import get_current_user
from app.core.config import settings
from app.models.user import User
from app.schemas.payments import CreatePaymentIntentRequest, PaymentIntentResponse
from app.services.payment_service import PaymentService, StripeEvent

router = APIRouter()


@router.post("/create-intent", response_model=PaymentIntentResponse)
async def create_payment_intent(
    request: CreatePaymentIntentRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    payment_service: Annotated[PaymentService, Depends(get_payment_service)],
) -> PaymentIntentResponse:
    """Create a payment intent for purchasing credits."""
    logger.info("Creating intent")
    return await payment_service.create_payment_intent(
        package_id=request.package_id,
        user_id=current_user.id,
    )


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    payment_service: Annotated[PaymentService, Depends(get_payment_service)],
) -> dict[str, bool]:
    """Handle Stripe webhook events."""
    if not settings.stripe_webhook_secret:
        raise HTTPException(status_code=500, detail="Stripe webhook secret not configured")

    # Get the webhook signature
    signature = request.headers.get("stripe-signature")
    if not signature:
        raise HTTPException(status_code=400, detail="Missing stripe-signature header")

    try:
        logger.info("Stripe webhook here")
        # Get the raw request body as bytes
        body = await request.body()

        # Verify webhook signature and construct the event
        raw_event = stripe.Webhook.construct_event(  # type: ignore
            payload=body.decode("utf-8"),  # Stripe expects the payload as a string
            sig_header=signature,
            secret=settings.stripe_webhook_secret,
        )
        event = cast(StripeEvent, raw_event)

        # Handle the event
        await payment_service.handle_webhook_event(event)

        return {"received": True}

    except stripe.StripeError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST) from err
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
