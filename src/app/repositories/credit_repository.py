"""Module for credit repository."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import selectinload

from app.core.database import DatabaseSessionManager
from app.core.exceptions import RepositoryError
from app.models.credits import (
    CreditBalance,
    CreditConfiguration,
    CreditPackage,
    CreditTransaction,
    Invoice,
    TransactionType,
)


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
        self, user_id: UUID, amount: int, balance_after: int, transaction_type: TransactionType, description: str
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
        transaction_type: TransactionType,
        description: str,
        transaction_metadata: dict[str, str | int] | None = None,
    ) -> CreditTransaction:
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
                await session.refresh(transaction)
                return transaction
        except SQLAlchemyError as e:
            raise RepositoryError(f"Failed to add credits: {e}") from e

    async def get_transactions(
        self,
        user_id: UUID,
        page: int = 1,
        limit: int = 10,
        type_filter: str = "important",
    ) -> tuple[list[CreditTransaction], int]:
        """Get paginated credit transactions for a user.

        Args:
            user_id: The ID of the user
            page: Page number (1-based)
            limit: Maximum number of transactions per page
            type_filter: Filter type ('important' or 'all')

        Returns:
            Tuple of (transactions list, total count)

        Raises:
            RepositoryError: If the database operation fails

        """
        try:
            async with self.db_session_manager.session() as session:
                # Base query
                base_query = (
                    select(CreditTransaction)
                    .options(selectinload(CreditTransaction.invoice))
                    .where(CreditTransaction.user_id == user_id)
                )

                # Apply type filter
                if type_filter == "important":
                    base_query = base_query.where(
                        (
                            CreditTransaction.transaction_type.in_(
                                [TransactionType.PURCHASE, TransactionType.SIGNUP_BONUS]
                            )
                        )
                        | (
                            (CreditTransaction.transaction_type == TransactionType.USAGE)
                            & (CreditTransaction.amount < -10)
                        )
                    )

                # Get total count
                count_query = select(func.count()).select_from(base_query.subquery())
                total_count = await session.execute(count_query)
                total_count = total_count.scalar_one()

                # Get paginated results
                offset = (page - 1) * limit
                stmt = base_query.order_by(CreditTransaction.created_at.desc()).limit(limit).offset(offset)
                result = await session.execute(stmt)
                transactions = list(result.scalars().all())

                return transactions, total_count
        except SQLAlchemyError as e:
            raise RepositoryError(f"Failed to fetch transactions: {e}") from e

    async def get_usage_data(
        self,
        user_id: UUID,
        start_date: datetime,
        end_date: datetime | None = None,
    ) -> list[dict[str, datetime | int]]:
        """Get daily credit usage data for a user.

        Args:
            user_id: The ID of the user
            start_date: Start date for the usage data
            end_date: Optional end date for the usage data

        Returns:
            List of daily usage data points

        Raises:
            RepositoryError: If the database operation fails

        """
        try:
            async with self.db_session_manager.session() as session:
                # Create the date_trunc expression once to reuse
                date_trunc_expr = func.date_trunc("day", CreditTransaction.created_at).label("date")

                stmt = (
                    select(
                        date_trunc_expr,
                        func.sum(CreditTransaction.amount).label("credits"),
                    )
                    .where(
                        CreditTransaction.user_id == user_id,
                        CreditTransaction.transaction_type == "usage",
                        CreditTransaction.created_at >= start_date,
                    )
                    .group_by(date_trunc_expr)
                    .order_by(date_trunc_expr)
                )

                if end_date:
                    stmt = stmt.where(CreditTransaction.created_at <= end_date)

                result = await session.execute(stmt)
                return [{"date": row.date, "credits": abs(row.credits)} for row in result.all()]
        except SQLAlchemyError as e:
            raise RepositoryError(f"Failed to fetch usage data: {e}") from e

    async def get_usage_sum(
        self,
        user_id: UUID,
        start_date: datetime,
        end_date: datetime | None = None,
    ) -> int:
        """Get total credit usage for a user within a date range.

        Args:
            user_id: The ID of the user
            start_date: Start date for the usage sum
            end_date: Optional end date for the usage sum

        Returns:
            Total credits used in the period

        Raises:
            RepositoryError: If the database operation fails

        """
        try:
            async with self.db_session_manager.session() as session:
                stmt = select(func.sum(CreditTransaction.amount)).where(
                    CreditTransaction.user_id == user_id,
                    CreditTransaction.transaction_type == "usage",
                    CreditTransaction.created_at >= start_date,
                )

                if end_date:
                    stmt = stmt.where(CreditTransaction.created_at <= end_date)

                result = await session.execute(stmt)
                usage_sum = result.scalar_one_or_none()
                return abs(usage_sum) if usage_sum else 0
        except SQLAlchemyError as e:
            raise RepositoryError(f"Failed to fetch usage sum: {e}") from e

    async def get_total_purchased_credits(self, user_id: UUID) -> int:
        """Get total credits ever purchased by a user.

        Args:
            user_id: The ID of the user

        Returns:
            Total credits purchased

        Raises:
            RepositoryError: If the database operation fails

        """
        try:
            async with self.db_session_manager.session() as session:
                stmt = select(func.sum(CreditTransaction.amount)).where(
                    CreditTransaction.user_id == user_id,
                    CreditTransaction.transaction_type == "purchase",
                )
                result = await session.execute(stmt)
                total = result.scalar_one_or_none()
                return total if total else 0
        except SQLAlchemyError as e:
            raise RepositoryError(f"Failed to fetch total purchased credits: {e}") from e

    async def get_invoice(self, user_id: UUID, invoice_id: UUID) -> Invoice | None:
        """Get an invoice by ID, ensuring it belongs to the user.

        Args:
            user_id: The ID of the user
            invoice_id: The ID of the invoice

        Returns:
            The invoice if found and owned by the user, None otherwise

        Raises:
            RepositoryError: If the database operation fails

        """
        try:
            async with self.db_session_manager.session() as session:
                stmt = select(Invoice).where(
                    Invoice.id == invoice_id,
                    Invoice.user_id == user_id,
                )
                result = await session.execute(stmt)
                return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            raise RepositoryError(f"Failed to fetch invoice: {e}") from e

    async def create_invoice(
        self,
        user_id: UUID,
        transaction_id: UUID,
        stripe_invoice_id: str,
    ) -> Invoice:
        """Create a new invoice record.

        Args:
            user_id: The ID of the user
            transaction_id: The ID of the related credit transaction
            stripe_invoice_id: The Stripe invoice ID

        Returns:
            The created invoice

        Raises:
            RepositoryError: If the database operation fails

        """
        try:
            async with self.db_session_manager.session() as session:
                invoice = Invoice(
                    user_id=user_id,
                    transaction_id=transaction_id,
                    stripe_invoice_id=stripe_invoice_id,
                )
                session.add(invoice)
                await session.commit()
                await session.refresh(invoice)
                return invoice
        except SQLAlchemyError as e:
            raise RepositoryError(f"Failed to create invoice: {e}") from e
