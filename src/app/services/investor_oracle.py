"""Service to orchestrate investor matching and LLM processing with streaming responses."""

from collections.abc import AsyncGenerator
from typing import Any

from fastapi import HTTPException
from fastapi.responses import StreamingResponse
from loguru import logger
from openai import AsyncOpenAI
from supabase import Client

from app.schemas.investor import InvestorMatchRequest, InvestorMatchResponse
from app.services.investor_finder import InvestorFinder


class InvestorOracle:
    """Orchestrates investor matching and LLM processing with streaming responses."""

    def __init__(
        self,
        investor_finder: InvestorFinder,
        supabase: Client,
        openai_client: AsyncOpenAI,
    ) -> None:
        """Initialize InvestorOracle with required dependencies.

        Args:
            investor_finder: Service for finding matching investors using Pydantic AI
            supabase: Supabase client for database operations
            openai_client: OpenAI client for embeddings

        """
        self.investor_finder = investor_finder
        self.supabase = supabase
        self.openai_client = openai_client

    async def process_request(
        self,
        request: InvestorMatchRequest,
    ) -> StreamingResponse:
        """Process an investor match request and stream results.

        Args:
            request: The investor match request containing search criteria
            supabase: Supabase client for database operations
            openai_client: OpenAI client for embeddings

        Returns:
            StreamingResponse containing processed investor matches

        Raises:
            HTTPException: If processing fails

        """
        try:
            return StreamingResponse(
                self._stream_matches(request),
                media_type="text/event-stream",
            )
        except Exception as exc:
            logger.error(f"Failed to process investor match request: {exc}")
            raise HTTPException(
                status_code=500,
                detail="Failed to process investor matches",
            ) from exc

    async def _stream_matches(
        self,
        request: InvestorMatchRequest,
    ) -> AsyncGenerator[str, Any]:
        """Stream processed investor matches.

        Args:
            request: The investor match request
            supabase: Supabase client
            openai_client: OpenAI client for embeddings

        Yields:
            Processed investor match responses as SSE events

        """
        try:
            # Create company context if provided in request
            company_context = None
            if request.company_context is not None:
                company_context = request.company_context

            # Generate embedding for similarity search using OpenAI
            embedding = await self.investor_finder.generate_embedding(
                prompt=request.prompt,
            )

            # Get matching investors using Supabase vector similarity search
            matches = self.investor_finder.get_investor_leads(
                supabase_client=self.supabase,
                embedding=embedding,
                threshold=request.threshold,
                limit=request.max_entries,
            )

            # Process and stream each match
            for match in matches:
                # Generate match reason using Pydantic AI
                reason = await self.investor_finder.generate_reason(
                    search_prompt=request.prompt,
                    investor=match.investor,
                    company_context=company_context,
                )

                # Create response object
                response = InvestorMatchResponse(
                    name=match.investor.name,
                    match_score=match.similarity,
                    reason=reason,
                    website=match.investor.website,
                    description=match.investor.description,
                    stage=match.investor.investment_stages,
                    industries=match.investor.industries,
                    check_size=match.investor.check_size.display if match.investor.check_size else None,
                    geographies=match.investor.geographies,
                )

                # Stream response as SSE event
                yield f"data: {response.model_dump_json()}\n\n"

        except Exception as exc:
            logger.error(f"Error streaming matches: {exc}")
            yield f"event: error\ndata: {exc!s}\n\n"
            return
