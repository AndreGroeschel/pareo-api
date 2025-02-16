"""Schemas for billing information."""

from uuid import UUID

from pydantic import BaseModel, constr


class BillingInfoBase(BaseModel):
    """Base schema for billing information."""

    name: str
    company_name: str | None = None
    vat_number: str | None = None
    address_line1: str
    address_line2: str | None = None
    city: str
    state: str | None = None
    postal_code: str
    country: constr(min_length=2, max_length=2)  # type: ignore


class BillingInfoCreate(BillingInfoBase):
    """Schema for creating billing information."""

    pass


class BillingInfoUpdate(BillingInfoBase):
    """Schema for updating billing information."""

    pass


class BillingInfoResponse(BillingInfoBase):
    """Schema for billing information response."""

    id: UUID
    user_id: UUID

    class Config:
        """Pydantic configuration."""

        from_attributes = True
