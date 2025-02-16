"""API endpoints for managing billing information."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from loguru import logger

from app.api.dependencies import get_billing_service
from app.core.auth.auth import get_current_user
from app.core.exceptions import BillingOperationError
from app.models.user import User
from app.schemas.billing import BillingInfoCreate, BillingInfoResponse, BillingInfoUpdate
from app.services.billing_service import BillingService

router = APIRouter(prefix="/billing", tags=["billing"])


@router.post("", response_model=BillingInfoResponse)
async def create_billing_info(
    billing_info: BillingInfoCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    billing_service: Annotated[BillingService, Depends(get_billing_service)],
) -> BillingInfoResponse:
    """Create billing information for the current user.

    Args:
        billing_info: The billing information to create
        current_user: The authenticated user
        billing_service: Service for managing billing operations

    Returns:
        The created billing information

    Raises:
        HTTPException: If there's an error creating the billing info

    """
    try:
        return await billing_service.create_billing_info(current_user.id, billing_info)
    except BillingOperationError as e:
        if "already exists" in str(e):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
        logger.error(f"Error creating billing info: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e


@router.get("/invoice/{invoice_id}", status_code=status.HTTP_200_OK)
async def get_invoice(
    invoice_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    billing_service: Annotated[BillingService, Depends(get_billing_service)],
) -> Response:
    """Get invoice by ID.

    Args:
        invoice_id: The ID of the invoice to retrieve
        current_user: The authenticated user
        billing_service: Service for managing billing operations

    Returns:
        The invoice PDF content

    Raises:
        HTTPException: If there's an error fetching the invoice

    """
    try:
        _, invoice_pdf_url = await billing_service.get_invoice(current_user.id, invoice_id)
        return Response(
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
            headers={"Location": invoice_pdf_url},
        )
    except BillingOperationError as e:
        if "not found" in str(e):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
        if "not available" in str(e):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
        logger.error(f"Error fetching invoice: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e


@router.get("", response_model=BillingInfoResponse)
async def get_billing_info(
    current_user: Annotated[User, Depends(get_current_user)],
    billing_service: Annotated[BillingService, Depends(get_billing_service)],
) -> BillingInfoResponse:
    """Get billing information for the current user.

    Args:
        current_user: The authenticated user
        billing_service: Service for managing billing operations

    Returns:
        The user's billing information

    Raises:
        HTTPException: If there's an error fetching the billing info

    """
    try:
        return await billing_service.get_billing_info(current_user.id)
    except BillingOperationError as e:
        if "not found" in str(e):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
        logger.error(f"Error fetching billing info: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e


@router.put("", response_model=BillingInfoResponse)
async def update_billing_info(
    billing_info: BillingInfoUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    billing_service: Annotated[BillingService, Depends(get_billing_service)],
) -> BillingInfoResponse:
    """Update billing information for the current user.

    Args:
        billing_info: The new billing information
        current_user: The authenticated user
        billing_service: Service for managing billing operations

    Returns:
        The updated billing information

    Raises:
        HTTPException: If there's an error updating the billing info

    """
    try:
        return await billing_service.update_billing_info(current_user.id, billing_info)
    except BillingOperationError as e:
        if "not found" in str(e):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
        logger.error(f"Error updating billing info: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e
