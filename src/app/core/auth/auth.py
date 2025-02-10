"""Authentication utilities for verifying JWT tokens."""

from typing import Annotated, Any

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from loguru import logger

from app.core.config import settings

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
