"""Authentication utilities for verifying JWT tokens."""

from datetime import datetime
from typing import Annotated, Any

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from loguru import logger
from sqlalchemy import select

from app.api.dependencies import get_credit_repository, get_db_session_manager, get_user_repository
from app.core.config import settings
from app.core.database import DatabaseSessionManager
from app.core.exceptions import UserOperationError
from app.models.user import ClerkWebhookEvent, User  # type: ignore
from app.repositories.credit_repository import CreditRepository
from app.repositories.user_repository import UserRepository
from app.services.clerk_user_sync_service import ClerkUserSyncService

security = HTTPBearer()


async def verify_token(credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)]) -> dict[str, Any]:
    """Verify Clerk JWT token and return payload.

    Args:
        credentials: The bearer token credentials

    Returns:
        Dict: The decoded token payload with user information

    Raises:
        HTTPException: If token is invalid or expired

    """
    try:
        raw_key = settings.clerk_pem_public_key
        public_key = f"-----BEGIN PUBLIC KEY-----\n{raw_key}\n-----END PUBLIC KEY-----"

        logger.debug(f"Public key format: {public_key[:50]}...")
        logger.debug(f"Public key format: {settings.clerk_pem_public_key[:100]}...")
        payload = jwt.decode(credentials.credentials, key=public_key, algorithms=["RS256"])
        return payload
    except jwt.ExpiredSignatureError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired") from e
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from e


async def get_current_user(
    token_payload: Annotated[dict[str, Any], Depends(verify_token)],
    db: Annotated[DatabaseSessionManager, Depends(get_db_session_manager)],
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
    credit_repo: Annotated[CreditRepository, Depends(get_credit_repository)],
) -> User:
    """Get the current authenticated user.

    If the user exists in Clerk (valid JWT) but not in our database,
    creates the user using the same logic as the webhook handler.

    Args:
        token_payload: The decoded JWT token payload
        db: Database session manager
        user_repo: User repository
        credit_repo: Credit repository

    Returns:
        User: The current authenticated user

    Raises:
        HTTPException: If user is not found or creation fails

    """
    try:
        clerk_id = token_payload.get("sub")
        if not clerk_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
            )

        async with db.session() as session:
            result = await session.execute(select(User).where(User.clerk_id == clerk_id))
            user = result.scalar_one_or_none()

            if user is None:
                # User exists in Clerk but not in our database
                # Create user using the same logic as webhook handler
                user_sync_service = ClerkUserSyncService(user_repo, credit_repo)

                # Fetch user data from Clerk API
                clerk_user = await user_sync_service.get_clerk_user(clerk_id)

                # Create webhook event
                webhook_event = ClerkWebhookEvent(
                    data=clerk_user, object="user", type="user.created", timestamp=int(datetime.now().timestamp())
                )

                # Create user with same logic as webhook
                user_id = await user_sync_service.sync_new_user(webhook_event)

                # Fetch the newly created user
                result = await session.execute(select(User).where(User.id == user_id))
                user = result.scalar_one()

            return user
    except UserOperationError as e:
        logger.error(f"Failed to create user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(f"Unexpected error in get_current_user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred",
        ) from e
