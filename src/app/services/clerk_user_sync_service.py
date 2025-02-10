# src/app/services/clerk_user_sync_service.py
"""Service for synchronizing user data from Clerk webhooks."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import text

from app.core.exceptions import UserOperationError
from app.schemas.user import ClerkWebhookEvent, UserCreate, UserUpdate
from app.services.database_session_manager import DatabaseSessionManager


class ClerkUserSyncService:
    """Service for synchronizing user data from Clerk webhook events.

    This service handles the mirroring of user data from Clerk's authentication service
    to our local database, including user creation, updates, and deletion events.
    """

    def __init__(self, db: DatabaseSessionManager) -> None:
        """Initialize ClerkUserSyncService with a database session manager."""
        self.db = db

    async def sync_new_user(self, webhook_data: ClerkWebhookEvent) -> UUID:
        """Create a new user record from Clerk webhook data.

        Args:
            webhook_data: Validated user data received from Clerk webhook

        Returns:
            UUID of the newly created user

        Raises:
            UserOperationError: If required Clerk data is missing or sync fails

        """
        try:
            user_uuid = uuid4()
            user_data = webhook_data.data

            if not user_data.email_addresses:
                raise UserOperationError("No email addresses provided")

            email = next(
                (e.email_address for e in user_data.email_addresses if e.id == user_data.primary_email_address_id),
                None,
            )
            if email is None:
                raise UserOperationError("Primary email address not found in email addresses list")

            user_create = UserCreate(
                id=user_uuid,
                clerk_id=user_data.id,
                email=email,
                name=f"{user_data.first_name or ''} {user_data.last_name or ''}".strip(),
            )

            async with self.db.session() as session:
                await session.execute(
                    text("""
                        INSERT INTO users (id, clerk_id, email, name)
                        VALUES (:uuid, :clerk_id, :email, :name)
                    """),
                    {
                        "uuid": user_create.id,
                        "clerk_id": user_create.clerk_id,
                        "email": user_create.email,
                        "name": user_create.name,
                    },
                )
                await session.commit()

            return user_uuid
        except Exception as e:
            raise UserOperationError(f"Failed to create user: {e!s}") from e

    async def sync_user_updates(self, webhook_data: ClerkWebhookEvent) -> None:
        """Update existing user record from Clerk webhook data.

        Args:
            webhook_data: Validated updated user data received from Clerk webhook

        Raises:
            UserOperationError: If required Clerk data is missing or sync fails

        """
        try:
            user_data = webhook_data.data

            if not user_data.email_addresses:
                raise UserOperationError("No email addresses provided")

            email = next(
                (e.email_address for e in user_data.email_addresses if e.id == user_data.primary_email_address_id),
                None,
            )
            if email is None:
                raise UserOperationError("Primary email address not found in email addresses list")

            user_update = UserUpdate(
                email=email,
                name=f"{user_data.first_name or ''} {user_data.last_name or ''}".strip(),
            )

            async with self.db.session() as session:
                await session.execute(
                    text("""
                        UPDATE users
                        SET email = :email, name = :name
                        WHERE clerk_id = :clerk_id
                    """),
                    {
                        "clerk_id": user_data.id,
                        "email": user_update.email,
                        "name": user_update.name,
                    },
                )
                await session.commit()
        except Exception as e:
            raise UserOperationError(f"Failed to update user: {e!s}") from e

    async def sync_user_deletion(self, clerk_id: str) -> None:
        """Mark user as deleted when deleted in Clerk.

        Args:
            clerk_id: Clerk's user ID for the deleted user

        Raises:
            UserOperationError: If deletion sync fails

        """
        try:
            async with self.db.session() as session:
                await session.execute(
                    text("""
                        UPDATE users
                        SET deleted_at = :now
                        WHERE clerk_id = :clerk_id
                    """),
                    {"clerk_id": clerk_id, "now": datetime.now(UTC)},
                )
                await session.commit()
        except Exception as e:
            raise UserOperationError(f"Failed to delete user: {e!s}") from e
