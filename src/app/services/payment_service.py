"""Service for handling payment operations."""

from typing import TypedDict, cast
from uuid import UUID

import stripe
from fastapi import HTTPException
from loguru import logger

from app.core.config import settings
from app.repositories.credit_repository import CreditRepository
from app.schemas.payments import PaymentIntentResponse


class StripeMetadata(TypedDict):
    """Type for Stripe metadata."""

    user_id: str
    package_id: str
    credits: str


class StripePaymentIntent(TypedDict):
    """Type for Stripe payment intent."""

    client_secret: str
    amount: int
    currency: str
    metadata: StripeMetadata
    id: str


class StripeEventData(TypedDict):
    """Type for Stripe event data."""

    object: StripePaymentIntent


class StripeEvent(TypedDict):
    """Type for Stripe event."""

    type: str
    data: StripeEventData


class PaymentService:
    """Service for handling payment operations."""

    def __init__(self, credit_repository: CreditRepository) -> None:
        """Initialize payment service."""
        self.credit_repository = credit_repository
        if not settings.stripe_secret_key:
            raise ValueError("stripe_secret_key is not set")
        stripe.api_key = settings.stripe_secret_key

    async def create_payment_intent(self, package_id: UUID, user_id: UUID) -> PaymentIntentResponse:
        """Create a Stripe payment intent for credit purchase."""
        logger.info("creating payment intent")
        # Get the credit package
        credit_package = await self.credit_repository.get_credit_package(package_id)
        if not credit_package:
            raise HTTPException(status_code=404, detail="Credit package not found")

        if not credit_package.is_active:
            raise HTTPException(status_code=400, detail="Credit package is not active")

        try:
            # Create a payment intent with Stripe
            intent = cast(
                StripePaymentIntent,
                stripe.PaymentIntent.create(
                    amount=credit_package.price_cents,
                    currency=credit_package.currency,
                    metadata={
                        "user_id": str(user_id),
                        "package_id": str(package_id),
                        "credits": str(credit_package.credits),
                    },
                ),
            )

            return PaymentIntentResponse(
                client_secret=intent["client_secret"],
                amount=intent["amount"],
                currency=intent["currency"],
            )

        except stripe.StripeError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e

    async def handle_webhook_event(self, event: StripeEvent) -> None:
        """Handle Stripe webhook events."""
        if event["type"] == "payment_intent.succeeded":
            payment_intent = event["data"]["object"]

            # Extract metadata
            user_id = UUID(payment_intent["metadata"]["user_id"])
            credits = int(payment_intent["metadata"]["credits"])

            # Add credits to user's balance
            await self.credit_repository.add_credits(
                user_id=user_id,
                amount=credits,
                transaction_type="purchase",
                description="Credit purchase via Stripe",
                transaction_metadata={
                    "payment_intent_id": payment_intent["id"],
                    "amount_paid": payment_intent["amount"],
                    "currency": payment_intent["currency"],
                },
            )
