"""Service for synchronizing user data from Clerk webhooks."""

from uuid import UUID, uuid4

import httpx
from loguru import logger

from app.core.config import settings
from app.core.exceptions import RepositoryError, UserOperationError
from app.models.credits import TransactionType
from app.models.user import ClerkUserData, ClerkWebhookEvent, UserParams, UserUpdate
from app.repositories.credit_repository import CreditRepository
from app.repositories.user_repository import UserRepository


class ClerkUserSyncService:
    """Service for synchronizing user data from Clerk webhook events."""

    def __init__(self, user_repo: UserRepository, credit_repo: CreditRepository) -> None:
        """Initialize the service with repositories."""
        self.user_repo = user_repo
        self.credit_repo = credit_repo
        self.clerk_base_url = settings.clerk_base_url

    async def get_clerk_user(self, clerk_id: str) -> ClerkUserData:
        """Fetch user data from Clerk API.

        Args:
            clerk_id: The Clerk user ID

        Returns:
            ClerkUserData: The user data from Clerk

        Raises:
            UserOperationError: If the API request fails

        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.clerk_base_url}/users/{clerk_id}",
                    headers={"Authorization": f"Bearer {settings.clerk_secret_key}"},
                )
                response.raise_for_status()
                user_data = response.json()

                return ClerkUserData(
                    id=user_data["id"],
                    email_addresses=user_data["email_addresses"],
                    first_name=user_data.get("first_name"),
                    last_name=user_data.get("last_name"),
                    primary_email_address_id=user_data["primary_email_address_id"],
                )
        except Exception as e:
            logger.error(f"Failed to fetch user data from Clerk: {e}")
            raise UserOperationError(f"Failed to fetch user data from Clerk: {e}") from e

    async def sync_new_user(self, webhook_data: ClerkWebhookEvent) -> UUID:
        """Create a new user record from Clerk webhook data and initialize credits."""
        try:
            user_data = webhook_data.data

            if not user_data.email_addresses:
                raise UserOperationError("No email addresses provided")

            email = next(
                (e.email_address for e in user_data.email_addresses if e.id == user_data.primary_email_address_id),
                None,
            )
            if email is None:
                raise UserOperationError("Primary email address not found")

            name = f"{user_data.first_name or ''} {user_data.last_name or ''}".strip()

            # Check if user with this email already exists (including soft-deleted)
            existing_user = await self.user_repo.get_user_by_email(email)

            if existing_user:
                # Reactivate the existing user with new Clerk ID
                await self.user_repo.reactivate_user(existing_user.id, user_data.id, name)
                return existing_user.id

            # Create new user if no existing user found
            user_uuid = uuid4()
            user_params = UserParams(
                uuid=user_uuid,
                clerk_id=user_data.id,
                email=email,
                name=name,
            )

            # Create user
            await self.user_repo.create_user(user_params)

            # Get signup bonus amount from configuration
            signup_bonus = await self.credit_repo.get_signup_bonus()

            if signup_bonus > 0:
                # Initialize credit balance
                await self.credit_repo.create_credit_balance(user_params.uuid, signup_bonus, signup_bonus)

                # Record transaction
                await self.credit_repo.create_credit_transaction(
                    user_id=user_params.uuid,
                    amount=signup_bonus,
                    balance_after=signup_bonus,
                    transaction_type=TransactionType.SIGNUP_BONUS,
                    description="Welcome bonus credits",
                )

            return user_uuid

        except RepositoryError as e:
            logger.error(f"Repository error during user creation: {e}")
            raise UserOperationError(f"Failed to create user due to repository error: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error during user creation: {e}")
            raise UserOperationError(f"Failed to create user: {e}") from e

    async def sync_update_user(self, webhook_data: ClerkWebhookEvent) -> None:
        """Update an existing user record from Clerk webhook data."""
        try:
            user_data = webhook_data.data

            if not user_data.email_addresses:
                raise UserOperationError("No email addresses provided")

            email = next(
                (e.email_address for e in user_data.email_addresses if e.id == user_data.primary_email_address_id),
                None,
            )
            if email is None:
                raise UserOperationError("Primary email address not found")

            user_update = UserUpdate(
                email=email,
                name=f"{user_data.first_name or ''} {user_data.last_name or ''}".strip(),
            )

            # Update user
            await self.user_repo.update_user(user_data.id, user_update)

        except RepositoryError as e:
            logger.error(f"Repository error during user update: {e}")
            raise UserOperationError(f"Failed to update user due to repository error: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error during user update: {e}")
            raise UserOperationError(f"Failed to update user: {e}") from e

    async def sync_delete_user(self, clerk_id: str) -> None:
        """Mark a user as deleted when deleted in Clerk."""
        try:
            # Mark user as deleted
            await self.user_repo.delete_user(clerk_id)

        except RepositoryError as e:
            logger.error(f"Repository error during user deletion: {e}")
            raise UserOperationError(f"Failed to delete user due to repository error: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error during user deletion: {e}")
            raise UserOperationError(f"Failed to delete user: {e}") from e
