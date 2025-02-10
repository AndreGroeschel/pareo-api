"""Endpoint for credits."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_credit_service
from app.core.auth.auth import get_current_user
from app.core.exceptions import CreditOperationError
from app.models.user import User
from app.schemas.credits import CreditBalanceResponse
from app.services.credit_service import CreditService

router = APIRouter()


@router.get("/balance", response_model=CreditBalanceResponse)
async def get_credit_balance(
    current_user: Annotated[User, Depends(get_current_user)],
    credit_service: Annotated[CreditService, Depends(get_credit_service)],
) -> CreditBalanceResponse:
    """Get the current user's credit balance."""
    try:
        return await credit_service.get_credit_balance(current_user.id)
    except CreditOperationError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e
