"""Endpoint for credits."""

from collections.abc import Sequence
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_credit_service
from app.core.auth.auth import get_current_user
from app.core.exceptions import CreditOperationError
from app.models.user import User
from app.schemas.credits import CreditBalanceResponse, CreditPackageResponse
from app.services.credit_service import CreditService

router = APIRouter()


@router.get("/balance", response_model=CreditBalanceResponse)
async def get_credit_balance(
    current_user: Annotated[User, Depends(get_current_user)],
    credit_service: Annotated[CreditService, Depends(get_credit_service)],
) -> CreditBalanceResponse:
    """Get the current user's credit balance.

    Args:
        current_user: The authenticated user requesting their balance
        credit_service: Service for managing credit-related operations

    """
    try:
        return await credit_service.get_credit_balance(current_user.id)
    except CreditOperationError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e


@router.get("/currencies", response_model=list[str])
async def get_available_currencies(
    credit_service: Annotated[CreditService, Depends(get_credit_service)],
) -> list[str]:
    """Get list of currencies that have active packages.

    Args:
        credit_service: Service for managing credit-related operations

    """
    try:
        return await credit_service.get_available_currencies()
    except CreditOperationError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e


@router.get("/packages", response_model=list[CreditPackageResponse])
async def get_credit_packages(
    credit_service: Annotated[CreditService, Depends(get_credit_service)],
    currency: str | None = None,
) -> Sequence[CreditPackageResponse]:
    """Get all available credit packages.

    Args:
        credit_service: Service for managing credit-related operations
        currency: Optional currency code to filter packages by (e.g. 'usd', 'eur')

    """
    try:
        return await credit_service.get_credit_packages(currency)
    except CreditOperationError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e
