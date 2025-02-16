"""Models for the credit system."""

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .user import User


class TransactionType(str, Enum):
    """Enum for credit transaction types."""

    PURCHASE = "purchase"
    USAGE = "usage"
    SIGNUP_BONUS = "signup_bonus"


class FeatureCost(Base):
    """Stores the credit cost for different features."""

    __tablename__ = "feature_costs"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    feature_key: Mapped[str] = mapped_column(String(100), unique=True)
    name: Mapped[str] = mapped_column(String(255))
    credits_cost: Mapped[int] = mapped_column(Integer)
    description: Mapped[str | None] = mapped_column(Text)
    internal_cost_cents: Mapped[int | None] = mapped_column(Integer)
    is_active: Mapped[bool | None] = mapped_column(Boolean, default=True)


class CreditPackage(Base):
    """Defines available credit purchase options."""

    __tablename__ = "credit_packages"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(255))
    credits: Mapped[int] = mapped_column(Integer)
    price_cents: Mapped[int] = mapped_column(Integer)
    currency: Mapped[str] = mapped_column(String(3))
    tier: Mapped[str] = mapped_column(String(50))
    savings_percentage: Mapped[int | None] = mapped_column(Integer)
    is_active: Mapped[bool | None] = mapped_column(Boolean, default=True)


class CreditTransaction(Base):
    """Records all credit-related activities."""

    __tablename__ = "credit_transactions"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    amount: Mapped[int] = mapped_column(Integer)
    balance_after: Mapped[int] = mapped_column(Integer)
    transaction_type: Mapped[TransactionType] = mapped_column(String(50))
    feature_key: Mapped[str | None] = mapped_column(ForeignKey("feature_costs.feature_key", ondelete="SET NULL"))
    description: Mapped[str | None] = mapped_column(Text)
    transaction_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSONB)

    user = relationship("User", back_populates="credit_transactions")
    feature = relationship("FeatureCost")
    invoice = relationship("Invoice", back_populates="transaction", uselist=False)


class CreditBalance(Base):
    """Maintains current credit status for each user."""

    __tablename__ = "credit_balances"

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    balance: Mapped[int] = mapped_column(Integer, default=0)
    lifetime_credits: Mapped[int] = mapped_column(Integer, default=0)
    tier: Mapped[str] = mapped_column(String(50), default="basic")
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user = relationship("User", back_populates="credit_balance")


class CreditConfiguration(Base):
    """System-wide credit configuration settings."""

    __tablename__ = "credit_configurations"

    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    value: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class Invoice(Base):
    """Model for credit purchase invoices.

    This model stores minimal information needed to retrieve and verify ownership of Stripe invoices.
    The actual invoice data and PDF are retrieved from Stripe when needed.
    """

    __tablename__ = "credit_invoices"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    transaction_id: Mapped[UUID] = mapped_column(ForeignKey("credit_transactions.id", ondelete="CASCADE"))
    stripe_invoice_id: Mapped[str] = mapped_column(String(255), unique=True)
    created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=func.now())

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="invoices")
    transaction: Mapped["CreditTransaction"] = relationship("CreditTransaction", back_populates="invoice")
