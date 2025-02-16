"""Provides FastAPI dependency injection configurations for the Pareo API.

It contains dependency providers that handle the creation and injection of services
and configurations needed throughout the application. The dependencies are designed
to be efficient through caching and proper resource management.
"""

from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from openai import AsyncOpenAI
from pydantic_ai.models.openai import OpenAIModel

from app.core.config import get_settings
from app.core.database import DatabaseSessionManager
from app.repositories.billing_repository import BillingRepository
from app.repositories.credit_repository import CreditRepository
from app.repositories.user_repository import UserRepository
from app.services.billing_service import BillingService
from app.services.clerk_user_sync_service import ClerkUserSyncService
from app.services.credit_service import CreditService
from app.services.investor_finder import InvestorFinder
from app.services.investor_oracle import InvestorOracle
from app.services.payment_service import PaymentService


@lru_cache
def get_openai_client() -> AsyncOpenAI:
    """Create and cache an OpenAI client instance.

    Returns:
        AsyncOpenAI: Configured OpenAI client instance.

    """
    settings = get_settings()
    return AsyncOpenAI(api_key=settings.openai_api_key)


@lru_cache
def get_reasoning_model() -> OpenAIModel:
    """Create and cache an OpenAI model instance.

    Returns:
        OpenAIModel: Configured OpenAI model instance.

    """
    settings = get_settings()
    return OpenAIModel(
        settings.reasoning_model, base_url=settings.openrouter_base_url, api_key=settings.openrouter_api_key
    )


@lru_cache
def get_db_session_manager() -> DatabaseSessionManager:
    """Centralized session manager instance."""
    settings = get_settings()
    return DatabaseSessionManager(settings.database_url, {"pool_pre_ping": True, "pool_size": 20, "max_overflow": 10})


@lru_cache
def get_user_repository(
    db_session_manager: Annotated[DatabaseSessionManager, Depends(get_db_session_manager)],
) -> UserRepository:
    """Dependency provider for the UserRepository."""
    return UserRepository(db_session_manager)


@lru_cache
def get_credit_repository(
    db_session_manager: Annotated[DatabaseSessionManager, Depends(get_db_session_manager)],
) -> CreditRepository:
    """Dependency provider for the CreditRepository."""
    return CreditRepository(db_session_manager)


@lru_cache
def get_credit_service(
    credit_repo: Annotated[CreditRepository, Depends(get_credit_repository)],
) -> CreditService:
    """Dependency provider for the CreditService."""
    return CreditService(credit_repo)


@lru_cache
def get_billing_repository(
    db_session_manager: Annotated[DatabaseSessionManager, Depends(get_db_session_manager)],
) -> BillingRepository:
    """Dependency provider for the BillingRepository."""
    return BillingRepository(db_session_manager)


@lru_cache
def get_billing_service(
    billing_repo: Annotated[BillingRepository, Depends(get_billing_repository)],
) -> BillingService:
    """Dependency provider for the BillingService."""
    return BillingService(billing_repo)


@lru_cache
def get_payment_service(
    credit_repo: Annotated[CreditRepository, Depends(get_credit_repository)],
    billing_service: Annotated[BillingService, Depends(get_billing_service)],
) -> PaymentService:
    """Dependency provider for the PaymentService."""
    return PaymentService(credit_repo, billing_service)


@lru_cache
def get_clerk_sync_service(
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
    credit_repo: Annotated[CreditRepository, Depends(get_credit_repository)],
) -> ClerkUserSyncService:
    """Dependency provider for the CreditRepository."""
    return ClerkUserSyncService(user_repo, credit_repo)


@lru_cache
def get_investor_finder() -> InvestorFinder:
    """Dependency provider for the InvestorFinder service.

    This function creates and caches an instance of InvestorFinder with the necessary
    configuration from application settings. The caching ensures we don't create
    unnecessary instances of the service.

    Returns:
        InvestorFinder: A configured instance of the InvestorFinder service.

    """
    settings = get_settings()
    openai = get_openai_client()
    reasoning_model = get_reasoning_model()
    return InvestorFinder(
        openai_client=openai,
        reasoning_model=reasoning_model,
        embedding_model_name=settings.embedding_model,
        db_session_manager=get_db_session_manager(),
    )


@lru_cache
def get_investor_oracle() -> InvestorOracle:
    """Dependency provider for the InvestorOracle service.

    This function creates and caches an instance of InvestorOracle with the necessary
    dependencies. The caching ensures we don't create unnecessary instances of the service.

    Returns:
        InvestorOracle: A configured instance of the InvestorOracle service.

    """
    investor_finder = get_investor_finder()
    openai = get_openai_client()
    return InvestorOracle(
        investor_finder=investor_finder,
        openai_client=openai,
    )
