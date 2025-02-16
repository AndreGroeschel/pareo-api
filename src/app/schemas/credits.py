"""Schemas for credits."""

from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, PositiveInt


class SpendCreditsRequest(BaseModel):
    """Schema for spend credits request.

    Attributes:
        amount: Number of credits to spend (must be positive)

    """

    amount: Annotated[PositiveInt, Field(description="Number of credits to spend")]


class SpendCreditsResponse(BaseModel):
    """Schema for spend credits response.

    Attributes:
        success: Whether the operation was successful
        remaining_credits: Number of credits remaining after spend
        transaction_id: ID of the created transaction

    """

    success: bool
    remaining_credits: int
    transaction_id: UUID

    model_config = ConfigDict(from_attributes=True)


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


class CreditTransactionResponse(BaseModel):
    """Schema for credit transaction response.

    Attributes:
        id: Transaction identifier
        date: Transaction date
        type: Type of transaction (purchase, usage, refund, bonus)
        amount: Number of credits involved
        description: Transaction description
        metadata: Additional transaction data (e.g., invoice ID)

    """

    id: UUID
    date: datetime
    type: str
    amount: int
    description: str
    metadata: dict[str, str] | None
    invoice_id: UUID | None

    model_config = ConfigDict(from_attributes=True)


class CreditUsageData(BaseModel):
    """Schema for credit usage data point.

    Attributes:
        date: Date of usage
        credits: Number of credits used

    """

    date: datetime
    credits: int

    model_config = ConfigDict(from_attributes=True)


class CreditStatsResponse(BaseModel):
    """Schema for credit statistics response.

    Attributes:
        available_credits: Current available credits
        used_this_month: Credits used in current month
        purchased_total: Total credits purchased
        lifetime_usage: Total credits used

    """

    available_credits: int
    used_this_month: int
    purchased_total: int
    lifetime_usage: int

    model_config = ConfigDict(from_attributes=True)


class PaginationInfo(BaseModel):
    """Schema for pagination information.

    Attributes:
        currentPage: Current page number
        totalPages: Total number of pages
        totalItems: Total number of items
        itemsPerPage: Number of items per page

    """

    currentPage: int
    totalPages: int
    totalItems: int
    itemsPerPage: int

    model_config = ConfigDict(from_attributes=True)


class TransactionsResponse(BaseModel):
    """Schema for transactions list response.

    Attributes:
        transactions: List of credit transactions
        usage_data: Credit usage over time
        pagination: Pagination information

    """

    transactions: list[CreditTransactionResponse]
    usage_data: list[CreditUsageData]
    pagination: PaginationInfo

    model_config = ConfigDict(from_attributes=True)
