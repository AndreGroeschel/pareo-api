"""Repository for managing billing information."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from app.core.database import DatabaseSessionManager
from app.core.exceptions import RepositoryError
from app.models.billing_info import BillingInfo
from app.models.credits import Invoice as CreditInvoice
from app.schemas.billing import BillingInfoCreate, BillingInfoUpdate


class BillingRepository:
    """Repository for managing billing information."""

    def __init__(self, db_session_manager: DatabaseSessionManager) -> None:
        """Initialize billing repository with a database session manager.

        Args:
            db_session_manager: The database session manager.

        """
        self.db_session_manager = db_session_manager

    async def create(self, user_id: UUID, billing_info: BillingInfoCreate) -> BillingInfo:
        """Create billing information for a user.

        Args:
            user_id: The ID of the user
            billing_info: The billing information to create

        Returns:
            The created billing information

        Raises:
            RepositoryError: If the database operation fails

        """
        try:
            async with self.db_session_manager.session() as session:
                db_billing_info = BillingInfo(user_id=user_id, **billing_info.model_dump())
                session.add(db_billing_info)
                await session.commit()
                await session.refresh(db_billing_info)
                return db_billing_info
        except SQLAlchemyError as e:
            raise RepositoryError(f"Failed to create billing info: {e}") from e

    async def get_by_user_id(self, user_id: UUID) -> BillingInfo | None:
        """Get billing information by user ID.

        Args:
            user_id: The ID of the user

        Returns:
            The billing information if found, None otherwise

        Raises:
            RepositoryError: If the database operation fails

        """
        try:
            async with self.db_session_manager.session() as session:
                stmt = select(BillingInfo).where(BillingInfo.user_id == user_id)
                result = await session.execute(stmt)
                return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            raise RepositoryError(f"Failed to fetch billing info: {e}") from e

    async def get_by_stripe_customer_id(self, stripe_customer_id: str) -> BillingInfo | None:
        """Get billing information by Stripe customer ID.

        Args:
            stripe_customer_id: The Stripe customer ID

        Returns:
            The billing information if found, None otherwise

        Raises:
            RepositoryError: If the database operation fails

        """
        try:
            async with self.db_session_manager.session() as session:
                stmt = select(BillingInfo).where(BillingInfo.stripe_customer_id == stripe_customer_id)
                result = await session.execute(stmt)
                return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            raise RepositoryError(f"Failed to fetch billing info: {e}") from e

    async def update(self, billing_info: BillingInfo, update_data: BillingInfoUpdate) -> BillingInfo:
        """Update billing information.

        Args:
            billing_info: The billing information to update
            update_data: The new billing information data

        Returns:
            The updated billing information

        Raises:
            RepositoryError: If the database operation fails

        """
        try:
            async with self.db_session_manager.session() as session:
                # Merge the detached instance into the session
                billing_info = await session.merge(billing_info)

                for field, value in update_data.model_dump(exclude_unset=True).items():
                    setattr(billing_info, field, value)

                await session.commit()
                await session.refresh(billing_info)
                return billing_info
        except SQLAlchemyError as e:
            raise RepositoryError(f"Failed to update billing info: {e}") from e

    async def update_stripe_customer_id(self, billing_info: BillingInfo, stripe_customer_id: str) -> BillingInfo:
        """Update Stripe customer ID.

        Args:
            billing_info: The billing information to update
            stripe_customer_id: The new Stripe customer ID

        Returns:
            The updated billing information

        Raises:
            RepositoryError: If the database operation fails

        """
        try:
            async with self.db_session_manager.session() as session:
                # Merge the detached instance into the session
                billing_info = await session.merge(billing_info)

                billing_info.stripe_customer_id = stripe_customer_id
                await session.commit()
                await session.refresh(billing_info)
                return billing_info
        except SQLAlchemyError as e:
            raise RepositoryError(f"Failed to update Stripe customer ID: {e}") from e

    async def get_invoice(self, user_id: UUID, invoice_id: UUID) -> CreditInvoice:
        """Get invoice by ID and user ID.

        Args:
            user_id: The ID of the user
            invoice_id: The ID of the invoice

        Returns:
            The invoice if found

        Raises:
            RepositoryError: If the database operation fails

        """
        try:
            async with self.db_session_manager.session() as session:
                stmt = select(CreditInvoice).where(CreditInvoice.id == invoice_id, CreditInvoice.user_id == user_id)
                result = await session.execute(stmt)
                invoice = result.scalar_one_or_none()
                if not invoice:
                    raise RepositoryError("Invoice not found")
                return invoice
        except SQLAlchemyError as e:
            raise RepositoryError(f"Failed to fetch invoice: {e}") from e
