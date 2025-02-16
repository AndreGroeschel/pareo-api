"""Service for handling payment operations."""

from typing import Any, TypedDict, cast
from uuid import UUID

import stripe
from fastapi import HTTPException
from loguru import logger

from app.core.config import settings
from app.models.credits import TransactionType
from app.repositories.credit_repository import CreditRepository
from app.schemas.payments import PaymentIntentResponse
from app.services.billing_service import BillingService


class StripeMetadata(TypedDict):
    """Type for Stripe metadata."""

    user_id: str
    package_id: str
    credits: str


class StripeInvoice(TypedDict):
    """Type for Stripe invoice."""

    id: str


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

    def __init__(
        self,
        credit_repository: CreditRepository,
        billing_service: BillingService,
    ) -> None:
        """Initialize payment service."""
        self.credit_repository = credit_repository
        self.billing_service = billing_service
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

            # Add credits to user's balance and get the transaction
            transaction = await self.credit_repository.add_credits(
                user_id=user_id,
                amount=credits,
                transaction_type=TransactionType.PURCHASE,
                description="Credit purchase via Stripe",
                transaction_metadata={
                    "payment_intent_id": payment_intent["id"],
                    "amount_paid": str(payment_intent["amount"]),
                    "currency": payment_intent["currency"],
                },
            )

            try:
                # Get or create Stripe customer
                billing_info = await self.billing_service.get_billing_model(user_id)
                if billing_info and billing_info.stripe_customer_id:
                    customer_id = billing_info.stripe_customer_id
                    logger.info(f"Using existing Stripe customer: {customer_id}")
                    customer = cast(Any, stripe.Customer.retrieve(customer_id))
                elif billing_info:
                    # Create customer with billing info
                    logger.info(f"Creating Stripe customer for user {user_id}")
                    customer = cast(
                        Any,
                        stripe.Customer.create(
                            metadata={"user_id": str(user_id)},
                            name=billing_info.name,  # Always use the billing name
                            tax_id_data=[{"type": "eu_vat", "value": billing_info.vat_number}]
                            if billing_info.vat_number
                            else [],
                            address={
                                "line1": billing_info.address_line1,
                                "line2": billing_info.address_line2 or "",
                                "city": billing_info.city,
                                "state": billing_info.state or "",
                                "postal_code": billing_info.postal_code,
                                "country": billing_info.country,
                            }
                            if billing_info.address_line1
                            else "",
                        ),
                    )
                    # Save Stripe customer ID
                    await self.billing_service.update_stripe_customer_id(billing_info, customer.id)
                    logger.info(f"Customer created with ID: {customer.id}")
                else:
                    # Create basic customer if no billing info exists
                    logger.info(f"Creating basic Stripe customer for user {user_id}")
                    customer = cast(
                        Any,
                        stripe.Customer.create(
                            metadata={"user_id": str(user_id)},
                            description=f"Customer for user {user_id}",
                        ),
                    )
                    logger.info(f"Basic customer created with ID: {customer.id}")

                # Create an invoice item
                logger.info("Creating invoice item")
                stripe.InvoiceItem.create(
                    customer=customer.id,
                    amount=payment_intent["amount"],
                    currency=payment_intent["currency"],
                    description=f"Credit purchase: {credits} credits",
                )

                # Create and finalize invoice
                logger.info("Creating invoice")
                invoice = cast(
                    Any,
                    stripe.Invoice.create(
                        customer=customer.id,
                        auto_advance=True,  # Auto-finalize the invoice
                    ),
                )
                logger.info(f"Invoice created with ID: {invoice.id}")

                # Pay the invoice with the payment intent
                logger.info("Paying invoice with payment intent")
                stripe.Invoice.pay(
                    invoice.id,
                    paid_out_of_band=True,  # Mark as paid without additional charge
                )

                # Cast to our type
                invoice_data = cast(StripeInvoice, {"id": invoice.id})
                logger.info(f"Creating invoice record with Stripe invoice ID: {invoice_data['id']}")

                # Create invoice record
                await self.credit_repository.create_invoice(
                    user_id=user_id,
                    transaction_id=transaction.id,
                    stripe_invoice_id=invoice_data["id"],
                )
                logger.info("Invoice record created successfully")
            except Exception as e:
                logger.error(f"Error handling invoice creation: {e!s}")
                raise
