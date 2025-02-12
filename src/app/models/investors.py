"""Models for investor-related tables."""

from datetime import datetime

from pgvector.sqlalchemy import Vector  # type: ignore
from sqlalchemy import ARRAY, BigInteger, ForeignKey, Index, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class Investor(Base):
    """Investor model."""

    __tablename__ = "investors"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    website: Mapped[str | None] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text)
    location: Mapped[str | None] = mapped_column(Text)
    contact_email: Mapped[str | None] = mapped_column(Text)
    contact_phone: Mapped[str | None] = mapped_column(Text)
    contact_form_url: Mapped[str | None] = mapped_column(Text)
    contact_name: Mapped[str | None] = mapped_column(Text)
    identified_email: Mapped[str | None] = mapped_column(Text)
    crawl_date: Mapped[datetime | None] = mapped_column()
    content_hash: Mapped[str | None] = mapped_column(Text)
    investment_stages: Mapped[list[str] | None] = mapped_column(ARRAY(Text))
    check_size: Mapped[dict | None] = mapped_column(JSONB)  # type: ignore
    industries: Mapped[list[str] | None] = mapped_column(ARRAY(Text))
    geographies: Mapped[list[str] | None] = mapped_column(ARRAY(Text))
    team: Mapped[dict | None] = mapped_column(JSONB)  # type: ignore
    portfolio: Mapped[dict | None] = mapped_column(JSONB)  # type: ignore
    preferred_contact_methods: Mapped[list[str] | None] = mapped_column(ARRAY(Text))
    investment_thesis: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(15), nullable=False)

    # Relationships
    team_members = relationship("TeamMember", back_populates="investor", passive_deletes=True)
    portfolio_companies = relationship("PortfolioCompany", back_populates="investor", passive_deletes=True)
    chunks = relationship("InvestorChunk", back_populates="investor", passive_deletes=True)

    __table_args__ = (Index("investors_active_status_idx", "id", postgresql_where=text("status = 'active'")),)


class TeamMember(Base):
    """Team member model."""

    __tablename__ = "team_members"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    investor_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("investors.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(Text, nullable=False)
    role: Mapped[str | None] = mapped_column(Text)
    linkedin_url: Mapped[str | None] = mapped_column(Text)
    focus_areas: Mapped[list[str] | None] = mapped_column(ARRAY(Text))

    investor = relationship("Investor", back_populates="team_members")


class PortfolioCompany(Base):
    """Portfolio company model."""

    __tablename__ = "portfolio_companies"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    investor_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("investors.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(Text, nullable=False)
    website: Mapped[str | None] = mapped_column(Text)
    industry: Mapped[str | None] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text)
    investment_year: Mapped[str | None] = mapped_column(String)

    investor = relationship("Investor", back_populates="portfolio_companies")


class InvestorChunk(Base):
    """Investor chunk model with vector embeddings."""

    __tablename__ = "investor_chunks"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    investor_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("investors.id", ondelete="CASCADE"))
    chunk_type: Mapped[str | None] = mapped_column(Text)
    chunk_text: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(1536))  # Specified vector size
    chunk_metadata: Mapped[dict | None] = mapped_column(JSONB, server_default=text("'{}'::jsonb"))  # type: ignore
    chunk_hash: Mapped[str | None] = mapped_column(String)

    investor = relationship("Investor", back_populates="chunks")

    __table_args__ = (
        Index(
            "investor_chunks_embedding_idx",
            "embedding",
            postgresql_using="ivfflat",
            postgresql_with={"lists": 100},
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )
