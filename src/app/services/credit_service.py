"""Service for credits."""

from uuid import UUID

from loguru import logger

from app.core.exceptions import CreditOperationError, RepositoryError
from app.repositories.credit_repository import CreditRepository
from app.schemas.credits import CreditBalanceResponse


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
        except Exception as e:
            logger.error(f"Unexpected error while fetching credit balance: {e}")
            raise CreditOperationError(f"Failed to fetch credit balance: {e}") from e
