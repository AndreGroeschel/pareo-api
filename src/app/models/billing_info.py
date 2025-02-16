"""Models for billing information."""

from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class BillingInfo(Base):
    """Billing information model.

    Attributes:
        id: Primary key UUID
        user_id: Foreign key to User
        name: Name for billing (individual's name or company contact)
        company_name: Optional company name for business customers
        vat_number: VAT registration number
        address_line1: Primary address line
        address_line2: Secondary address line (optional)
        city: City name
        state: State or region (optional)
        postal_code: Postal/ZIP code
        country: Two-letter country code
        stripe_customer_id: ID of the customer in Stripe
        user: Relationship to User model

    """

    __tablename__ = "billing_info"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    name: Mapped[str] = mapped_column(String(255))
    company_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    vat_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    address_line1: Mapped[str] = mapped_column(String(255))
    address_line2: Mapped[str | None] = mapped_column(String(255), nullable=True)
    city: Mapped[str] = mapped_column(String(100))
    state: Mapped[str | None] = mapped_column(String(100), nullable=True)
    postal_code: Mapped[str] = mapped_column(String(20))
    country: Mapped[str] = mapped_column(String(2))  # ISO 3166-1 alpha-2 country code
    stripe_customer_id: Mapped[str | None] = mapped_column(String(255), nullable=True, unique=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="billing_info")
