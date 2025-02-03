"""Service to find investors who match funding requirements."""

from typing import Any

from loguru import logger
from openai import AsyncOpenAI
from pydantic import BaseModel
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from supabase import Client

from app.schemas.investor import CheckSize, CompanyContext, Investor


class InvestorMatchResult(BaseModel):
    """Holds result of an investor that is similar to the request."""

    investor: Investor
    similarity: float
    raw_data: dict[str, Any]


class InvestorFinder:
    """Finds investors via similarity search."""

    def __init__(
        self,
        reasoning_model: OpenAIModel,
        openai_client: AsyncOpenAI,
        embedding_model_name: str,
        max_tokens: int = 64000,
        retries: int = 3,
    ) -> None:
        """Initialize the InvestorLeadsProcessor.

        Args:
            reasoning_model (str): Pydantic AI model to use for reasoning about investor match
            openai_client: OpenAI client (for embeddings),
            embedding_model_name (str): Name of the model to use for embeddings
            max_tokens (int, optional): Maximum tokens per request. Defaults to 64000
            retries (int, optional): Number of retry attempts for failed requests. Defaults to 3

        Note:
            The processor requires valid API credentials and will validate them during initialization.

        """
        logger.info("🚀 Initializing InvestorLeadsProcessor")
        try:
            self.openai_client = openai_client
            self.embedding_model_name = embedding_model_name
            self.agent = Agent(reasoning_model, retries=retries)
            self.max_tokens = max_tokens
            logger.debug("Successfully initialized LLM processor")
        except Exception as e:
            logger.error(f"Failed to initialize processor: {e!s}")
            raise

    async def generate_embedding(self, prompt: str) -> list[float]:
        """Generate embedding vector for search prompt."""
        try:
            logger.debug(f"Generating embedding for prompt: {prompt}...")
            embedding = await self.openai_client.embeddings.create(input=prompt, model=self.embedding_model_name)
            query_embedding = embedding.data[0].embedding
            logger.info(f"✅ Generated embedding vector (length: {len(query_embedding)})")
            return query_embedding
        except Exception as e:
            logger.error(f"❌ Embedding generation failed: {e!s}")
            raise RuntimeError("Embedding generation failed") from e

    async def generate_reason(
        self, search_prompt: str, investor: Investor, company_context: CompanyContext | None = None
    ) -> str:
        """Generate match reason using LLM with validated investor and company data.

        Args:
            search_prompt: The search criteria used to find investors
            investor: The investor to analyze
            company_context: Optional company details to enhance the matching analysis

        """
        try:
            # Build structured prompt from validated investor data
            investor_details = self._format_investor_details(investor)
            company_details = self._format_company_details(company_context) if company_context else ""

            full_prompt = (
                "Generate a concise explanation of why this investor would be a good match. "
                "Consider alignment between the company and investor in terms of:"
                "\n- Industry focus and expertise"
                "\n- Investment stage and check size"
                "\n- Geographic preferences"
                "\n- Value add and strategic fit"
                "\nBe specific about why this investor would be valuable for this company."
                f"\n\nSearch criteria: {search_prompt}"
                f"\n\nCompany details:\n{company_details}"
                f"\n\nInvestor details:\n{investor_details}"
            )

            result = await self.agent.run(full_prompt)
            logger.debug(f"Generated reason: {result.data}")
            return result.data
        except Exception as e:
            logger.error(f"❌ Reason generation failed: {e!s}")
            return "Reason not available"

    def _format_investor_details(self, investor: Investor) -> str:
        """Format validated investor data for LLM prompt."""
        return (
            f"Name: {investor.name}\n"
            f"Description: {investor.description or 'No description available'}\n"
            f"Investment thesis: {investor.investment_thesis or 'No thesis available'}\n"
            f"Industries: {', '.join(investor.industries)}\n"
            f"Geographies: {', '.join(investor.geographies)}\n"
            f"Stage: {', '.join(investor.investment_stages) if investor.investment_stages else 'N/A'}\n"
            f"Check Size: {self._format_check_size(investor.check_size)}"
        )

    def _format_company_details(self, company_context: CompanyContext | None) -> str:
        """Format company context for LLM prompt."""
        if not company_context:
            return ""

        benefits_list = "\n- ".join(company_context.key_benefits)
        return (
            f"Company: {company_context.company_name}\n"
            f"Value Proposition: {company_context.value_prop}\n"
            f"Key Benefits:\n- {benefits_list}\n"
            f"Stage: {company_context.stage}\n"
            f"Location: {company_context.location}\n"
            f"Check Size: {company_context.check_request_size}"
        )

    def _format_check_size(self, check_size: CheckSize | None) -> str:
        """Format check size information."""
        if not check_size:
            return "N/A"
        return check_size.display or f"{check_size.min}-{check_size.max} {check_size.currency}"

    def get_investor_leads(
        self, supabase_client: Client, embedding: list[float], threshold: float, limit: int
    ) -> list[InvestorMatchResult]:
        """Retrieve and validates investor leads from Supabase."""
        try:
            logger.debug(f"Querying Supabase with threshold {threshold}, limit {limit}")

            result = supabase_client.rpc(  # type: ignore
                "get_investor_leads",
                {"query_embedding": embedding, "match_threshold": threshold, "match_count": limit},
            ).execute()

            logger.info(f"🔍 Found {len(result.data)} potential investors")  # type: ignore
            logger.info(f"🔍 Found {len(result.data)} potential investors")  # type: ignore
            return self._validate_investors(result.data)  # type: ignore
        except Exception as e:
            logger.error(f"❌ Failed to fetch investor leads: {e!s}")
            raise RuntimeError("Supabase query failed") from e

    def _validate_investors(self, raw_data: list[dict[str, Any]]) -> list[InvestorMatchResult]:
        """Convert raw data to validated match results."""
        validated: list[InvestorMatchResult] = []
        for idx, item in enumerate(raw_data):
            try:
                similarity = item.get("similarity", 0.0)
                investor = Investor.model_validate(item)
                validated.append(InvestorMatchResult(investor=investor, similarity=similarity, raw_data=item))
            except Exception as e:
                logger.error(f"Skipping invalid investor data at index {idx}: {e!s}")
                logger.debug(f"Problematic data: {item}")
        return validated
