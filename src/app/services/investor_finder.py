"""Service to find investors who match funding requirements."""

from typing import Any

from loguru import logger
from openai import AsyncOpenAI
from pydantic import BaseModel
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from app.core.database import DatabaseSessionManager
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
        db_session_manager: DatabaseSessionManager,
        max_tokens: int = 64000,
        retries: int = 3,
    ) -> None:
        """Initialize the InvestorLeadsProcessor with async database support."""
        logger.info("🚀 Initializing InvestorLeadsProcessor")
        try:
            self.openai_client = openai_client
            self.embedding_model_name = embedding_model_name
            self.agent = Agent(reasoning_model, retries=retries)
            self.max_tokens = max_tokens
            self.session_manager = db_session_manager
            logger.debug("Successfully initialized LLM and database components")
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

    async def get_investor_leads(
        self, embedding: list[float], threshold: float, limit: int
    ) -> list[InvestorMatchResult]:
        """Retrieve and validate investor leads from the database."""
        try:
            logger.debug(f"Querying database with threshold {threshold}, limit {limit}")

            # Convert embedding list to PostgreSQL vector string format
            embedding_str = "[" + ",".join(map(str, embedding)) + "]"

            async with self.session_manager.session() as session:
                result = await session.execute(
                    text("""
                        SELECT * FROM get_investor_leads(
                            CAST(:embedding AS vector(1536)),
                            :threshold,
                            :limit
                        )
                    """),
                    {
                        "embedding": embedding_str,  # Pass as string
                        "threshold": threshold,
                        "limit": limit,
                    },
                )

                rows = result.mappings().all()
                logger.info(f"🔍 Found {len(rows)} potential investors")
                return self._validate_investors([dict(row) for row in rows])

        except OperationalError as oe:
            logger.error(f"🚨 Database connection error: {oe!s}")
            raise RuntimeError("Database connection error") from oe
        except Exception as e:
            logger.error(f"❌ Failed to fetch investor leads: {e!s}")
            raise

    def _validate_investors(self, raw_data: list[dict[str, Any]]) -> list[InvestorMatchResult]:
        """Convert raw data to validated match results."""
        validated: list[InvestorMatchResult] = []
        for idx, item in enumerate(raw_data):
            try:
                similarity = item.get("similarity", 0.0)
                investor = Investor.model_validate(item)
                validated.append(InvestorMatchResult(investor=investor, similarity=similarity, raw_data=dict(item)))
            except Exception as e:
                logger.error(f"Skipping invalid investor data at index {idx}: {e!s}")
                logger.debug(f"Problematic data: {item}")
        return validated

    async def generate_reason(
        self, search_prompt: str, investor: Investor, company_context: CompanyContext | None = None
    ) -> str:
        """Generate match reason using LLM with validated investor and company data."""
        try:
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
