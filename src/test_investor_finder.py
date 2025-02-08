"""Test script for InvestorFinder functionality."""

import asyncio
import os

from dotenv import load_dotenv
from openai import AsyncOpenAI
from supabase import Client, create_client

from app.services.investor_finder import InvestorFinder, InvestorMatchResult


async def test_investor_finder() -> None:
    """Run a test search with the InvestorFinder."""
    # Load environment variables
    load_dotenv()

    # Initialize OpenAI client
    openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    # Initialize Supabase client
    supabase: Client = create_client(os.getenv("SUPABASE_URL", ""), os.getenv("SUPABASE_KEY", ""))

    # Initialize InvestorFinder
    finder = InvestorFinder(
        open_router_base_url=os.getenv("OPENROUTER_BASE_URL", ""),
        open_router_api_key=os.getenv("OPENROUTER_API_KEY", ""),
        reasoning_model_name=os.getenv("REASONING_MODEL", ""),
        embedding_model_name=os.getenv("EMBEDDING_MODEL", ""),
    )

    # Test search parameters
    search_prompt = (
        "Pre-Seed investor in Europe, Germany, Portugal, Greece for a startup in AI, "
        "proptech or real estate tech. Stage: Pre-Seed"
    )
    threshold = 0.6
    limit = 10

    try:
        # Generate embedding for search
        embedding = await finder.generate_embedding(search_prompt, openai_client)
        print(f"✅ Generated embedding vector (length: {len(embedding)})")

        # Get investor leads
        match_results: list[InvestorMatchResult] = finder.get_investor_leads(supabase, embedding, threshold, limit)
        print(f"\n🔍 Found {len(match_results)} matching investors:")

        # # Process each result
        # for idx, match_result in enumerate(match_results, 1):
        #     if not match_result.investor:
        #         continue
        #     reason = await finder.generate_reason(search_prompt, match_result.investor, company_context)

        #     print(f"\n{idx}. {match_result.investor.name} (Similarity Score: {match_result.similarity:.2f})")
        #     print(f"   Reason: {reason}")
        #     print(f"   Industries: {', '.join(match_result.investor.industries)}")
        #     print(
        #         f"   Stages: "
        #         f"{
        #             ', '.join(match_result.investor.investment_stages)
        #             if match_result.investor.investment_stages
        #             else 'N/A'
        #         }"
        #     )
        #     print(f"   Geographies: {', '.join(match_result.investor.geographies)}")

    except Exception as e:
        print(f"❌ Error during test: {e}")


if __name__ == "__main__":
    asyncio.run(test_investor_finder())
