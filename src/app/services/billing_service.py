"""Service for managing billing information."""

from uuid import UUID

import stripe
from loguru import logger
from stripe import StripeError

from app.core.config import settings
from app.core.exceptions import BillingOperationError, RepositoryError
from app.models.billing_info import BillingInfo
from app.models.credits import Invoice as CreditInvoice
from app.repositories.billing_repository import BillingRepository
from app.schemas.billing import BillingInfoCreate, BillingInfoResponse, BillingInfoUpdate


class BillingService:
    """Service for handling billing-related operations."""

    def __init__(self, billing_repo: BillingRepository) -> None:
        """Initialize the service with a billing repository."""
        self.billing_repo = billing_repo

    async def create_billing_info(self, user_id: UUID, billing_info: BillingInfoCreate) -> BillingInfoResponse:
        """Create billing information for a user.

        Args:
            user_id: The ID of the user
            billing_info: The billing information to create

        Returns:
            The created billing information

        Raises:
            BillingOperationError: If there's an error creating the billing info

        """
        try:
            # Check if billing info already exists
            existing_info = await self.billing_repo.get_by_user_id(user_id)
            if existing_info:
                raise BillingOperationError("Billing information already exists for this user")

            # Create new billing info
            db_billing_info = await self.billing_repo.create(user_id, billing_info)
            return BillingInfoResponse.model_validate(db_billing_info)

        except RepositoryError as e:
            logger.error(f"Repository error while creating billing info: {e}")
            raise BillingOperationError(f"Failed to create billing info: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error while creating billing info: {e}")
            raise BillingOperationError(f"Failed to create billing info: {e}") from e

    async def get_billing_info(self, user_id: UUID) -> BillingInfoResponse:
        """Get billing information for a user.

        Args:
            user_id: The ID of the user

        Returns:
            The user's billing information

        Raises:
            BillingOperationError: If there's an error fetching the billing info

        """
        try:
            billing_info = await self.billing_repo.get_by_user_id(user_id)
            if not billing_info:
                raise BillingOperationError("No billing information found for this user")

            return BillingInfoResponse.model_validate(billing_info)

        except RepositoryError as e:
            logger.error(f"Repository error while fetching billing info: {e}")
            raise BillingOperationError(f"Failed to fetch billing info: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error while fetching billing info: {e}")
            raise BillingOperationError(f"Failed to fetch billing info: {e}") from e

    async def get_billing_model(self, user_id: UUID) -> BillingInfo:
        """Get billing information model for a user.

        Args:
            user_id: The ID of the user

        Returns:
            The user's billing information model

        Raises:
            BillingOperationError: If there's an error fetching the billing info

        """
        try:
            billing_info = await self.billing_repo.get_by_user_id(user_id)
            if not billing_info:
                raise BillingOperationError("No billing information found for this user")

            return billing_info

        except RepositoryError as e:
            logger.error(f"Repository error while fetching billing info: {e}")
            raise BillingOperationError(f"Failed to fetch billing info: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error while fetching billing info: {e}")
            raise BillingOperationError(f"Failed to fetch billing info: {e}") from e

    async def update_billing_info(self, user_id: UUID, billing_info: BillingInfoUpdate) -> BillingInfoResponse:
        """Update billing information for a user.

        Args:
            user_id: The ID of the user
            billing_info: The new billing information

        Returns:
            The updated billing information

        Raises:
            BillingOperationError: If there's an error updating the billing info

        """
        try:
            # Get existing billing info
            existing_info = await self.billing_repo.get_by_user_id(user_id)
            if not existing_info:
                raise BillingOperationError("No billing information found for this user")

            # Update billing info
            updated_info = await self.billing_repo.update(existing_info, billing_info)
            return BillingInfoResponse.model_validate(updated_info)

        except RepositoryError as e:
            logger.error(f"Repository error while updating billing info: {e}")
            raise BillingOperationError(f"Failed to update billing info: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error while updating billing info: {e}")
            raise BillingOperationError(f"Failed to update billing info: {e}") from e

    async def update_stripe_customer_id(self, billing_info: BillingInfo, stripe_customer_id: str) -> BillingInfo:
        """Update Stripe customer ID.

        Args:
            billing_info: The billing information to update
            stripe_customer_id: The new Stripe customer ID

        Returns:
            The updated billing information

        Raises:
            BillingOperationError: If there's an error updating the Stripe customer ID

        """
        try:
            return await self.billing_repo.update_stripe_customer_id(billing_info, stripe_customer_id)
        except RepositoryError as e:
            logger.error(f"Repository error while updating Stripe customer ID: {e}")
            raise BillingOperationError(f"Failed to update Stripe customer ID: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error while updating Stripe customer ID: {e}")
            raise BillingOperationError(f"Failed to update Stripe customer ID: {e}") from e

    async def get_invoice(self, user_id: UUID, invoice_id: UUID) -> tuple[CreditInvoice, str]:
        """Get invoice by ID and user ID.

        Args:
            user_id: The ID of the user
            invoice_id: The ID of the invoice

        Returns:
            A tuple containing the invoice and the PDF URL

        Raises:
            BillingOperationError: If there's an error fetching the invoice

        """
        try:
            # Get the invoice from our database to verify ownership
            invoice = await self.billing_repo.get_invoice(user_id, invoice_id)

            try:
                # Get the invoice from Stripe with PDF URL
                stripe_invoice = stripe.Invoice.retrieve(
                    invoice.stripe_invoice_id,
                    api_key=settings.stripe_secret_key,
                )

                if not stripe_invoice.invoice_pdf:
                    raise BillingOperationError("Invoice PDF not available")

                if not stripe_invoice.invoice_pdf:
                    raise BillingOperationError("Invoice PDF not available")

                return invoice, stripe_invoice.invoice_pdf

            except StripeError as e:
                logger.error(f"Stripe error while fetching invoice: {e}")
                raise BillingOperationError(f"Failed to fetch invoice from Stripe: {e}") from e

        except RepositoryError as e:
            logger.error(f"Repository error while fetching invoice: {e}")
            raise BillingOperationError(f"Failed to fetch invoice: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error while fetching invoice: {e}")
            raise BillingOperationError(f"Failed to fetch invoice: {e}") from e
