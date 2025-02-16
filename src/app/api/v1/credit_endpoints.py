"""Endpoint for credits."""

from collections.abc import Sequence
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_credit_service
from app.core.auth.auth import get_current_user
from app.core.exceptions import CreditOperationError
from app.models.user import User
from app.schemas.credits import (
    CreditBalanceResponse,
    CreditPackageResponse,
    CreditStatsResponse,
    SpendCreditsRequest,
    SpendCreditsResponse,
    TransactionsResponse,
)
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


@router.get("/transactions", response_model=TransactionsResponse)
async def get_transactions(
    current_user: Annotated[User, Depends(get_current_user)],
    credit_service: Annotated[CreditService, Depends(get_credit_service)],
    page: int = 1,
    limit: int = 10,
    type: str = "important",
) -> TransactionsResponse:
    """Get user's credit transactions and usage data.

    Args:
        current_user: The authenticated user
        credit_service: Service for managing credit-related operations
        page: Page number (1-based)
        limit: Maximum number of transactions per page
        type: Filter type ('important' or 'all')

    """
    # Validate parameters
    if page < 1:
        raise HTTPException(status_code=400, detail="Page number must be greater than 0")
    if limit < 1 or limit > 100:
        raise HTTPException(status_code=400, detail="Limit must be between 1 and 100")
    if type not in ["important", "all"]:
        raise HTTPException(status_code=400, detail="Type must be 'important' or 'all'")

    try:
        return await credit_service.get_transactions_with_usage(
            user_id=current_user.id,
            page=page,
            limit=limit,
            type_filter=type,
        )
    except CreditOperationError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e


@router.get("/stats", response_model=CreditStatsResponse)
async def get_credit_stats(
    current_user: Annotated[User, Depends(get_current_user)],
    credit_service: Annotated[CreditService, Depends(get_credit_service)],
) -> CreditStatsResponse:
    """Get user's credit usage statistics.

    Args:
        current_user: The authenticated user
        credit_service: Service for managing credit-related operations

    """
    try:
        return await credit_service.get_credit_stats(current_user.id)
    except CreditOperationError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e


@router.post("/spend", response_model=SpendCreditsResponse)
async def spend_credits(
    request: SpendCreditsRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    credit_service: Annotated[CreditService, Depends(get_credit_service)],
) -> SpendCreditsResponse:
    """Spend credits from user's balance.

    Args:
        request: The spend credits request containing amount to spend
        current_user: The authenticated user
        credit_service: Service for managing credit-related operations

    Returns:
        Response containing success status, remaining credits and transaction ID

    Raises:
        HTTPException: If there's an error spending credits or insufficient balance

    """
    try:
        return await credit_service.spend_credits(
            user_id=current_user.id,
            amount=request.amount,
        )
    except CreditOperationError as e:
        if "Insufficient credits" in str(e):
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail=str(e),
            ) from e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e
