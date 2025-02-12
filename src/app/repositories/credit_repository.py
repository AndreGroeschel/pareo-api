"""Module for credit repository."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from app.core.database import DatabaseSessionManager
from app.core.exceptions import RepositoryError
from app.models.credits import CreditBalance, CreditConfiguration, CreditPackage, CreditTransaction


class CreditRepository:
    """Repository for credit-related database operations.

    Handles interactions with the database for CreditBalance, CreditConfiguration,
    and CreditTransaction models.
    """

    def __init__(self, db_session_manager: DatabaseSessionManager) -> None:
        """Initialize the CreditRepository with a database session manager.

        Args:
            db_session_manager: The database session manager.

        """
        self.db_session_manager = db_session_manager

    async def get_signup_bonus(self) -> int:
        """Get the configured signup bonus amount.

        Returns:
            The signup bonus amount.

        Raises:
            RepositoryError: If the database operation fails.

        """
        try:
            async with self.db_session_manager.session() as session:
                stmt = select(CreditConfiguration).where(
                    CreditConfiguration.key == "signup_bonus", CreditConfiguration.is_active
                )
                result = await session.execute(stmt)
                config = result.scalar_one_or_none()
                return config.value if config else 0
        except SQLAlchemyError as e:
            raise RepositoryError(f"Failed to retrieve signup bonus: {e}") from e

    async def create_credit_balance(self, user_id: UUID, balance: int, lifetime_credits: int) -> None:
        """Create a new credit balance for a user.

        Args:
            user_id: The ID of the user.
            balance: The initial credit balance.
            lifetime_credits: The total lifetime credits for the user.

        Raises:
            RepositoryError: If the database operation fails.

        """
        try:
            async with self.db_session_manager.session() as session:
                credit_balance = CreditBalance(
                    user_id=user_id,
                    balance=balance,
                    lifetime_credits=lifetime_credits,
                )
                session.add(credit_balance)
                await session.commit()
        except SQLAlchemyError as e:
            raise RepositoryError(f"Failed to create credit balance: {e}") from e

    async def create_credit_transaction(
        self, user_id: UUID, amount: int, balance_after: int, transaction_type: str, description: str
    ) -> None:
        """Create a new credit transaction.

        Args:
            user_id: The ID of the user.
            amount: The amount of the transaction.
            balance_after: The user's credit balance after the transaction.
            transaction_type: The type of the transaction.
            description: A description of the transaction.

        Raises:
            RepositoryError: If the database operation fails.

        """
        try:
            async with self.db_session_manager.session() as session:
                transaction = CreditTransaction(
                    user_id=user_id,
                    amount=amount,
                    balance_after=balance_after,
                    transaction_type=transaction_type,
                    description=description,
                )
                session.add(transaction)
                await session.commit()
        except SQLAlchemyError as e:
            raise RepositoryError(f"Failed to create credit transaction: {e}") from e

    async def get_credit_balance(self, user_id: UUID) -> CreditBalance | None:
        """Get the credit balance for a user."""
        try:
            async with self.db_session_manager.session() as session:
                stmt = select(CreditBalance).where(CreditBalance.user_id == user_id)
                result = await session.execute(stmt)
                return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            raise RepositoryError(f"Failed to fetch credit balance: {e}") from e

    async def get_active_packages(self, currency: str | None = None) -> list[CreditPackage]:
        """Get all active credit packages.

        Args:
            currency: Optional currency code to filter packages by (e.g. 'usd', 'eur')

        Returns:
            List of active credit packages ordered by credits amount.

        Raises:
            RepositoryError: If the database operation fails.

        """
        try:
            async with self.db_session_manager.session() as session:
                stmt = select(CreditPackage).where(CreditPackage.is_active.is_(True))
                if currency:
                    stmt = stmt.where(CreditPackage.currency == currency.lower())
                stmt = stmt.order_by(CreditPackage.credits)
                result = await session.execute(stmt)
                return list(result.scalars().all())
        except SQLAlchemyError as e:
            raise RepositoryError(f"Failed to fetch credit packages: {e}") from e

    async def get_available_currencies(self) -> list[str]:
        """Get list of currencies that have active packages.

        Returns:
            List of currency codes (e.g. ['usd', 'eur'])

        Raises:
            RepositoryError: If the database operation fails.

        """
        try:
            async with self.db_session_manager.session() as session:
                stmt = (
                    select(CreditPackage.currency)
                    .where(CreditPackage.is_active.is_(True))
                    .group_by(CreditPackage.currency)
                )
                result = await session.execute(stmt)
                return [r[0] for r in result.all()]
        except SQLAlchemyError as e:
            raise RepositoryError(f"Failed to fetch available currencies: {e}") from e

    async def get_credit_package(self, package_id: UUID) -> CreditPackage | None:
        """Get a credit package by ID."""
        try:
            async with self.db_session_manager.session() as session:
                stmt = select(CreditPackage).where(CreditPackage.id == package_id)
                result = await session.execute(stmt)
                return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            raise RepositoryError(f"Failed to fetch credit package: {e}") from e

    async def add_credits(
        self,
        user_id: UUID,
        amount: int,
        transaction_type: str,
        description: str,
        transaction_metadata: dict[str, str | int] | None = None,
    ) -> None:
        """Add credits to a user's balance and create a transaction record.

        Args:
            user_id: The ID of the user.
            amount: The amount of credits to add.
            transaction_type: The type of transaction.
            description: A description of the transaction.
            transaction_metadata: Optional metadata for the transaction.

        Raises:
            RepositoryError: If the database operation fails.

        """
        try:
            async with self.db_session_manager.session() as session:
                # Get current balance
                stmt = select(CreditBalance).where(CreditBalance.user_id == user_id)
                result = await session.execute(stmt)
                balance = result.scalar_one_or_none()

                if not balance:
                    raise RepositoryError(f"No credit balance found for user {user_id}")

                # Update balance
                new_balance = balance.balance + amount
                balance.balance = new_balance
                balance.lifetime_credits += amount if amount > 0 else 0

                # Create transaction record
                transaction = CreditTransaction(
                    user_id=user_id,
                    amount=amount,
                    balance_after=new_balance,
                    transaction_type=transaction_type,
                    description=description,
                    transaction_metadata=transaction_metadata,
                )
                session.add(transaction)

                await session.commit()
        except SQLAlchemyError as e:
            raise RepositoryError(f"Failed to add credits: {e}") from e
