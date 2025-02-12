"""Schemas for credits."""

from uuid import UUID

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


class CreditPackageResponse(BaseModel):
    """Schema for credit package response.

    Attributes:
        id: Package identifier
        name: Package name
        credits: Number of credits in package
        price_cents: Price in cents
        tier: Package tier (e.g., 'basic', 'premium')
        savings_percentage: Percentage of savings compared to base price
        is_active: Whether the package is currently available

    """

    id: UUID
    name: str
    credits: int
    price_cents: int
    currency: str
    tier: str
    savings_percentage: int | None
    is_active: bool

    model_config = ConfigDict(from_attributes=True)
