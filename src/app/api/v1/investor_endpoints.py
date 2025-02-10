"""API V1 Endpoints Module.

This module contains all the endpoint handlers for the v1 API.
It defines the core business logic for handling HTTP requests.
"""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from loguru import logger

from app.api.dependencies import get_investor_oracle
from app.core.auth.auth import verify_token
from app.schemas.investor import InvestorMatchRequest

router = APIRouter()


@router.post("/match", tags=["investors"])
async def match_investors(
    request: Request,
    investor_request: InvestorMatchRequest,
    token_data: Annotated[dict[str, Any], Depends(verify_token)],
) -> StreamingResponse:
    """Stream investor matches based on search criteria.

    This endpoint processes an investor match request and streams back results
    as they are processed. Each result includes match scoring and AI-generated
    reasoning for the match.

    Args:
        request: The raw FastAPI request object.
        investor_request (InvestorMatchRequest): The investor match request containing search criteria
        and company context.
        token_data (dict[str, Any]): The decoded JWT token data containing user information.

    Returns:
        StreamingResponse: Server-sent events stream of investor matches.

    Example:
        Request:
        ```json
        {
            "prompt": "Seed stage AI investors in Europe",
            "threshold": 0.7,
            "max_entries": 10,
            "company_context": {
                "company_name": "AI Solutions Ltd",
                "value_prop": "AI-powered business automation platform",
                "key_benefits": ["Increased efficiency", "Cost reduction", "Scalable solution"],
                "stage": "Seed",
                "location": "London, UK",
                "check_request_size": "2M"
            }
        }
        ```

        Response Stream Events:
        ```
        data: {
            "name": "Example VC",
            "match_score": 0.85,
            "reason": "Strong match due to focus on AI startups...",
            "website": "https://example.vc",
            "description": "Early stage AI/ML focused fund...",
            "stage": ["Seed", "Series A"],
            "industries": ["AI/ML", "Enterprise Software"],
            "check_size": "$500K-2M",
            "geographies": ["Europe"]
        }
        ```

    """
    # user = user or Depends(verify_token)
    body = await request.body()
    logger.debug(f"Raw request body: {body.decode()}")

    logger.debug("Token data contents:")
    for key, value in token_data.items():
        logger.debug(f"  {key}: {value}")

    user_id = token_data.get("sub")
    logger.debug(f"User ID from token: {user_id}")
    investor_oracle = get_investor_oracle()
    return await investor_oracle.process_request(request=investor_request)
