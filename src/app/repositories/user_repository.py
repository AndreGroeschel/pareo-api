"""Module for user repository."""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.exc import SQLAlchemyError

from app.core.database import DatabaseSessionManager
from app.core.exceptions import RepositoryError
from app.models.user import User, UserParams, UserUpdate


class UserRepository:
    """Repository for user-related database operations.

    Handles interactions with the database for User model, including creating,
    updating, and deleting users.
    """

    def __init__(self, db_session_manager: DatabaseSessionManager) -> None:
        """Initialize the UserRepository with a database session manager.

        Args:
            db_session_manager: The database session manager.

        """
        self.db_session_manager = db_session_manager

    async def get_user_by_email(self, email: str) -> User | None:
        """Get a user by email address, including soft-deleted users.

        Args:
            email: The email address to search for.

        Returns:
            The user if found, None otherwise.

        Raises:
            RepositoryError: If the database operation fails.

        """
        try:
            async with self.db_session_manager.session() as session:
                stmt = select(User).where(User.email == email)
                result = await session.execute(stmt)
                return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            raise RepositoryError(f"Failed to get user by email: {e}") from e

    async def create_user(self, user_params: "UserParams") -> UUID:
        """Create a new user in the database.

        Args:
            user_params: The parameters for creating the user.

        Returns:
            The UUID of the newly created user.

        Raises:
            RepositoryError: If the database operation fails.

        """
        try:
            async with self.db_session_manager.session() as session:
                user = User(
                    id=user_params.uuid,
                    clerk_id=user_params.clerk_id,
                    email=user_params.email,
                    name=user_params.name,
                )
                session.add(user)
                await session.commit()
                return user.id
        except SQLAlchemyError as e:
            raise RepositoryError(f"Failed to create user: {e}") from e

    async def update_user(self, clerk_id: str, user_update: UserUpdate) -> None:
        """Update an existing user in the database.

        Args:
            clerk_id: The Clerk ID of the user to update.
            user_update: The updated user information.

        Raises:
            RepositoryError: If the database operation fails.

        """
        try:
            async with self.db_session_manager.session() as session:
                stmt = (
                    update(User).where(User.clerk_id == clerk_id).values(email=user_update.email, name=user_update.name)
                )
                await session.execute(stmt)
                await session.commit()
        except SQLAlchemyError as e:
            raise RepositoryError(f"Failed to update user: {e}") from e

    async def delete_user(self, clerk_id: str) -> None:
        """Mark a user as deleted in the database.

        Args:
            clerk_id: The Clerk ID of the user to delete.

        Raises:
            RepositoryError: If the database operation fails.

        """
        try:
            async with self.db_session_manager.session() as session:
                stmt = update(User).where(User.clerk_id == clerk_id).values(deleted_at=datetime.now(UTC))
                await session.execute(stmt)
                await session.commit()
        except SQLAlchemyError as e:
            raise RepositoryError(f"Failed to delete user: {e}") from e

    async def reactivate_user(self, user_id: UUID, clerk_id: str, name: str) -> None:
        """Reactivate a soft-deleted user with a new Clerk ID.

        Args:
            user_id: The UUID of the user to reactivate.
            clerk_id: The new Clerk ID for the user.
            name: The updated name for the user.

        Raises:
            RepositoryError: If the database operation fails.

        """
        try:
            async with self.db_session_manager.session() as session:
                stmt = update(User).where(User.id == user_id).values(clerk_id=clerk_id, name=name, deleted_at=None)
                await session.execute(stmt)
                await session.commit()
        except SQLAlchemyError as e:
            raise RepositoryError(f"Failed to reactivate user: {e}") from e
