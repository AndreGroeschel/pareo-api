"""Authentication utilities for verifying JWT tokens."""

from typing import Annotated, Any

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from loguru import logger
from sqlalchemy import select

from app.api.dependencies import get_db_session_manager
from app.core.config import settings
from app.core.database import DatabaseSessionManager
from app.models.user import User

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
) -> User:
    """Get the current authenticated user.

    Args:
        token_payload: The decoded JWT token payload
        db: Database session manager

    Returns:
        User: The current authenticated user

    Raises:
        HTTPException: If user is not found

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
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found",
                )

            return user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        ) from e
