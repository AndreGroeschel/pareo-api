"""Schemas for payment-related operations."""

from uuid import UUID

from pydantic import BaseModel, Field


class CreatePaymentIntentRequest(BaseModel):
    """Request schema for creating a payment intent."""

    package_id: UUID = Field(..., description="ID of the credit package being purchased")


class PaymentIntentResponse(BaseModel):
    """Response schema for payment intent creation."""

    client_secret: str = Field(..., description="Client secret for the payment intent")
    amount: int = Field(..., description="Amount in cents")
    currency: str = Field(..., description="Currency code")
