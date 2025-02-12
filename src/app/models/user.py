"""Models for Clerk webhook data and user management.

This module defines Pydantic models for handling Clerk webhook events
and user data synchronization between Clerk and our application.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field
from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.credits import CreditBalance, CreditTransaction


class User(Base):
    """User model with Clerk authentication integration.

    Attributes:
        id: Primary key UUID
        name: User's full name
        clerk_id: Unique identifier from Clerk
        email: User's primary email address
        credit_balance: One-to-one relationship with user's credit balance
        credit_transactions: One-to-many relationship with credit transactions

    """

    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(255))
    clerk_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(255), index=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Credit system relationships
    credit_balance: Mapped[Optional["CreditBalance"]] = relationship(
        "CreditBalance", back_populates="user", uselist=False
    )
    credit_transactions: Mapped[list["CreditTransaction"]] = relationship(
        "CreditTransaction", back_populates="user", passive_deletes=True
    )


class ClerkEmailVerification(BaseModel):
    """Model for Clerk email verification status.

    Attributes:
        status: Verification status (e.g. "verified", "unverified")
        strategy: Verification method used (e.g. "ticket", "admin")
        attempts: Number of verification attempts made
        expire_at: When the verification expires

    """

    status: str
    strategy: str
    attempts: int | None = None
    expire_at: datetime | None = None


class LinkedToData(BaseModel):
    """Model for linked authentication data."""

    id: str
    type: str


class ClerkEmailAddress(BaseModel):
    """Model for Clerk email address data.

    Attributes:
        email_address: The actual email address
        id: Unique identifier for this email address
        verification: Email verification details
        linked_to: List of linked identifiers
        object: Type identifier from Clerk
        reserved: Whether this email is reserved

    """

    email_address: str
    id: str
    verification: ClerkEmailVerification
    linked_to: list[LinkedToData] = Field(default_factory=list)
    object: str
    reserved: bool | None = None


class ClerkUserData(BaseModel):
    """Model for Clerk user data received in webhooks.

    Attributes:
        id: Unique Clerk user identifier
        email_addresses: List of user's email addresses
        first_name: User's first name
        last_name: User's last name
        primary_email_address_id: ID of the primary email address
        deleted: Whether the user is deleted in Clerk

    """

    id: str
    email_addresses: list[ClerkEmailAddress] = Field(default_factory=list)
    first_name: str | None = None
    last_name: str | None = None
    primary_email_address_id: str | None = None
    deleted: bool | None = None


class ClerkWebhookEvent(BaseModel):
    """Model for incoming Clerk webhook events.

    Attributes:
        data: User data included in the webhook
        type: Event type (e.g. "user.created", "user.updated")
        object: Object type from Clerk
        timestamp: Unix timestamp of the event

    """

    data: ClerkUserData
    type: str
    object: str
    timestamp: int

    class Config:
        """Additional configuration data."""

        extra = "allow"  # Allow additional fields from Clerk


class UserCreate(BaseModel):
    """Model for creating a new user in our database.

    Attributes:
        id: UUID for the new user
        clerk_id: User's ID from Clerk
        email: User's primary email address
        name: User's full name

    """

    id: UUID
    clerk_id: str
    email: str
    name: str


class UserUpdate(BaseModel):
    """Model for updating an existing user.

    Attributes:
        email: Updated email address
        name: Updated full name

    """

    email: str
    name: str


class WebhookResponse(BaseModel):
    """Model for webhook processing response.

    Attributes:
        status: Status of the webhook processing ("created", "updated", "deleted", "ignored")
        user_id: UUID of the affected user (only for user creation)

    """

    status: str
    user_id: str | None = None


class UserParams(BaseModel):
    """Type-safe parameters for user creation."""

    uuid: UUID
    clerk_id: str
    email: str
    name: str
