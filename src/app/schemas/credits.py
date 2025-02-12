"""Schemas for credits."""

from pydantic import BaseModel, ConfigDict


class CreditBalanceResponse(BaseModel):
    """Schema for credit balance response.

    Attributes:
        balance: Current credit balance
        lifetime_credits: Total credits ever received
        tier: Current user tier (e.g., 'basic', 'premium')

    """

    balance: int
    lifetime_credits: int
    tier: str

    model_config = ConfigDict(from_attributes=True)
