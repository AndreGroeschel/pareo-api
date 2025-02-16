"""Service for credits."""

from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from uuid import UUID

from loguru import logger
from stripe import StripeError

from app.core.exceptions import CreditOperationError, RepositoryError
from app.models.credits import Invoice, TransactionType
from app.repositories.credit_repository import CreditRepository
from app.schemas.credits import (
    CreditBalanceResponse,
    CreditPackageResponse,
    CreditStatsResponse,
    CreditTransactionResponse,
    CreditUsageData,
    PaginationInfo,
    SpendCreditsResponse,
    TransactionsResponse,
)


class CreditService:
    """Service for handling credit-related operations."""

    def __init__(self, credit_repo: CreditRepository) -> None:
        """Initialize the service with a credit repository."""
        self.credit_repo = credit_repo

    async def get_credit_balance(self, user_id: UUID) -> CreditBalanceResponse:
        """Get the credit balance for a user."""
        try:
            # Retrieve the credit balance from the repository
            credit_balance = await self.credit_repo.get_credit_balance(user_id)
            if not credit_balance:
                raise CreditOperationError("Credit balance not found")

            # Convert the database model to a response schema
            return CreditBalanceResponse.model_validate(credit_balance)

        except RepositoryError as e:
            logger.error(f"Repository error while fetching credit balance: {e}")
            raise CreditOperationError(f"Failed to fetch credit balance: {e}") from e

    async def get_credit_packages(self, currency: str | None = None) -> Sequence[CreditPackageResponse]:
        """Get all active credit packages.

        Args:
            currency: Optional currency code to filter packages by (e.g. 'usd', 'eur')

        Returns:
            List of active credit packages.

        Raises:
            CreditOperationError: If there's an error fetching the packages.

        """
        try:
            packages = await self.credit_repo.get_active_packages(currency)
            return [CreditPackageResponse.model_validate(package) for package in packages]
        except RepositoryError as e:
            logger.error(f"Repository error while fetching credit packages: {e}")
            raise CreditOperationError(f"Failed to fetch credit packages: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error while fetching credit packages: {e}")
            raise CreditOperationError(f"Failed to fetch credit packages: {e}") from e

    async def get_available_currencies(self) -> list[str]:
        """Get list of currencies that have active packages.

        Returns:
            List of currency codes (e.g. ['usd', 'eur'])

        Raises:
            CreditOperationError: If there's an error fetching the currencies.

        """
        try:
            return await self.credit_repo.get_available_currencies()
        except RepositoryError as e:
            logger.error(f"Repository error while fetching currencies: {e}")
            raise CreditOperationError(f"Failed to fetch currencies: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error while fetching currencies: {e}")
            raise CreditOperationError(f"Failed to fetch currencies: {e}") from e

    async def get_transactions_with_usage(
        self,
        user_id: UUID,
        page: int = 1,
        limit: int = 10,
        type_filter: str = "important",
    ) -> TransactionsResponse:
        """Get user's credit transactions and usage data.

        Args:
            user_id: The ID of the user
            page: Page number (1-based)
            limit: Maximum number of transactions per page
            type_filter: Filter type ('important' or 'all')

        Returns:
            Combined transaction history and usage data with pagination info

        Raises:
            CreditOperationError: If there's an error fetching the data

        """
        try:
            # Get transactions with pagination and filtering
            transactions, total_count = await self.credit_repo.get_transactions(
                user_id=user_id,
                page=page,
                limit=limit,
                type_filter=type_filter,
            )

            # Get usage data for the last 30 days
            thirty_days_ago = datetime.now(UTC) - timedelta(days=30)
            usage_data = await self.credit_repo.get_usage_data(
                user_id=user_id,
                start_date=thirty_days_ago,
            )

            # Calculate pagination info
            total_pages = (total_count + limit - 1) // limit

            return TransactionsResponse(
                transactions=[
                    CreditTransactionResponse(
                        id=t.id,
                        date=t.created_at or datetime.now(UTC),  # Fallback if None
                        type=t.transaction_type,
                        amount=t.amount,
                        description=t.description or "",  # Fallback if None
                        metadata={
                            k: str(v) if isinstance(v, int | float) else v
                            for k, v in (t.transaction_metadata or {}).items()
                        },  # Convert numbers to strings and fallback if None
                        invoice_id=t.invoice.id if t.invoice else None,  # Include invoice ID if it exists
                    )
                    for t in transactions
                ],
                usage_data=[
                    CreditUsageData(
                        date=d["date"] if isinstance(d["date"], datetime) else datetime.now(UTC),
                        credits=d["credits"] if isinstance(d["credits"], int) else 0,
                    )
                    for d in usage_data
                ],
                pagination=PaginationInfo(
                    currentPage=page,
                    totalPages=total_pages,
                    totalItems=total_count,
                    itemsPerPage=limit,
                ),
            )

        except RepositoryError as e:
            logger.error(f"Repository error while fetching transactions: {e}")
            raise CreditOperationError(f"Failed to fetch transactions: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error while fetching transactions: {e}")
            raise CreditOperationError(f"Failed to fetch transactions: {e}") from e

    async def get_credit_stats(self, user_id: UUID) -> CreditStatsResponse:
        """Get user's credit usage statistics.

        Args:
            user_id: The ID of the user

        Returns:
            Credit usage statistics

        Raises:
            CreditOperationError: If there's an error fetching the stats

        """
        try:
            # Get current balance
            credit_balance = await self.credit_repo.get_credit_balance(user_id)
            if not credit_balance:
                raise CreditOperationError("Credit balance not found")

            # Get monthly usage
            first_of_month = datetime.now(UTC).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            monthly_usage = await self.credit_repo.get_usage_sum(
                user_id=user_id,
                start_date=first_of_month,
            )

            # Get total purchased credits
            total_purchased = await self.credit_repo.get_total_purchased_credits(user_id)

            # Calculate lifetime usage (total purchased + any bonuses - current balance)
            lifetime_usage = total_purchased - credit_balance.balance

            return CreditStatsResponse(
                available_credits=credit_balance.balance,
                used_this_month=monthly_usage,
                purchased_total=total_purchased,
                lifetime_usage=lifetime_usage,
            )

        except RepositoryError as e:
            logger.error(f"Repository error while fetching credit stats: {e}")
            raise CreditOperationError(f"Failed to fetch credit stats: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error while fetching credit stats: {e}")
            raise CreditOperationError(f"Failed to fetch credit stats: {e}") from e

    async def spend_credits(self, user_id: UUID, amount: int) -> SpendCreditsResponse:
        """Spend credits from a user's balance.

        Args:
            user_id: The ID of the user
            amount: The amount of credits to spend (positive number)

        Returns:
            Response containing success status, remaining credits and transaction ID

        Raises:
            CreditOperationError: If there's an error spending credits or insufficient balance

        """
        try:
            # Get current balance
            credit_balance = await self.credit_repo.get_credit_balance(user_id)
            if not credit_balance:
                raise CreditOperationError("Credit balance not found")

            # Check if user has enough credits
            if credit_balance.balance < amount:
                raise CreditOperationError("Insufficient credits")

            # Create transaction with negative amount to deduct credits
            transaction = await self.credit_repo.add_credits(
                user_id=user_id,
                amount=-amount,  # Negative amount to deduct credits
                transaction_type=TransactionType.USAGE,
                description="Credits spent",
            )

            return SpendCreditsResponse(
                success=True,
                remaining_credits=transaction.balance_after,
                transaction_id=transaction.id,
            )

        except RepositoryError as e:
            logger.error(f"Repository error while spending credits: {e}")
            raise CreditOperationError(f"Failed to spend credits: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error while spending credits: {e}")
            raise CreditOperationError(f"Failed to spend credits: {e}") from e

    async def get_invoice(self, user_id: UUID, invoice_id: UUID) -> Invoice:
        """Get invoice for a credit purchase.

        Args:
            user_id: The ID of the user
            invoice_id: The ID of the invoice to retrieve

        Returns:
            The invoice if found and owned by the user

        Raises:
            CreditOperationError: If the invoice is not found or unauthorized

        Raises:
            CreditOperationError: If there's an error fetching the invoice

        """
        try:
            # Verify the invoice belongs to the user
            invoice = await self.credit_repo.get_invoice(user_id, invoice_id)
            if not invoice:
                raise CreditOperationError("Invoice not found or unauthorized")

            return invoice

        except RepositoryError as e:
            logger.error(f"Repository error while fetching invoice: {e}")
            raise CreditOperationError(f"Failed to fetch invoice: {e}") from e
        except StripeError as e:
            logger.error(f"Stripe error while fetching invoice: {e}")
            raise CreditOperationError(f"Failed to fetch invoice from Stripe: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error while fetching invoice: {e}")
            raise CreditOperationError(f"Failed to fetch invoice: {e}") from e
