"""Create credit system tables.

Revision ID: 8fc8eca45073
Revises:
Create Date: 2025-02-10 22:20:52.065876

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "8fc8eca45073"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Create users table first
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("clerk_id", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_clerk_id"), "users", ["clerk_id"], unique=True)
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=False)

    # Create credit system tables
    op.create_table(
        "credit_packages",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("credits", sa.Integer(), nullable=False),
        sa.Column("price_cents", sa.Integer(), nullable=False),
        sa.Column("tier", sa.String(length=50), nullable=False),
        sa.Column("savings_percentage", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "feature_costs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("feature_key", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("credits_cost", sa.Integer(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("internal_cost_cents", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("feature_key"),
    )
    op.create_table(
        "credit_balances",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("balance", sa.Integer(), nullable=False),
        sa.Column("lifetime_credits", sa.Integer(), nullable=False),
        sa.Column("tier", sa.String(length=50), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id"),
    )
    op.create_table(
        "credit_transactions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("balance_after", sa.Integer(), nullable=False),
        sa.Column("transaction_type", sa.String(length=50), nullable=False),
        sa.Column("feature_key", sa.String(length=100), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("transaction_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["feature_key"], ["feature_costs.feature_key"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # Add timestamps to existing tables
    op.add_column(
        "investor_chunks",
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
    )
    op.alter_column(
        "investor_chunks",
        "created_at",
        existing_type=postgresql.TIMESTAMP(),
        type_=sa.DateTime(timezone=True),
        existing_nullable=True,
    )
    op.drop_constraint("investor_chunks_investor_id_fkey", "investor_chunks", type_="foreignkey")
    op.create_foreign_key("fk_investor_chunks_investor_id", "investor_chunks", "investors", ["investor_id"], ["id"], ondelete="CASCADE")

    op.add_column(
        "investors", sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True)
    )
    op.alter_column(
        "investors",
        "created_at",
        existing_type=postgresql.TIMESTAMP(),
        type_=sa.DateTime(timezone=True),
        existing_nullable=True,
    )

    op.add_column(
        "portfolio_companies",
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
    )
    op.alter_column(
        "portfolio_companies",
        "created_at",
        existing_type=postgresql.TIMESTAMP(),
        type_=sa.DateTime(timezone=True),
        existing_nullable=True,
    )
    op.drop_constraint("portfolio_companies_investor_id_fkey", "portfolio_companies", type_="foreignkey")
    op.create_foreign_key("fk_portfolio_companies_investor_id", "portfolio_companies", "investors", ["investor_id"], ["id"], ondelete="CASCADE")

    op.add_column(
        "team_members",
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
    )
    op.alter_column(
        "team_members",
        "created_at",
        existing_type=postgresql.TIMESTAMP(),
        type_=sa.DateTime(timezone=True),
        existing_nullable=True,
    )
    op.drop_constraint("team_members_investor_id_fkey", "team_members", type_="foreignkey")
    op.create_foreign_key("fk_team_members_investor_id", "team_members", "investors", ["investor_id"], ["id"], ondelete="CASCADE")


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table("credit_transactions")
    op.drop_table("credit_balances")
    op.drop_table("feature_costs")
    op.drop_table("credit_packages")

    # Remove timestamps from existing tables
    op.drop_constraint("fk_team_members_investor_id", "team_members", type_="foreignkey")
    op.create_foreign_key("team_members_investor_id_fkey", "team_members", "investors", ["investor_id"], ["id"])
    op.alter_column(
        "team_members",
        "created_at",
        existing_type=sa.DateTime(timezone=True),
        type_=postgresql.TIMESTAMP(),
        existing_nullable=True,
    )
    op.drop_column("team_members", "updated_at")

    op.drop_constraint("fk_portfolio_companies_investor_id", "portfolio_companies", type_="foreignkey")
    op.create_foreign_key(
        "portfolio_companies_investor_id_fkey", "portfolio_companies", "investors", ["investor_id"], ["id"]
    )
    op.alter_column(
        "portfolio_companies",
        "created_at",
        existing_type=sa.DateTime(timezone=True),
        type_=postgresql.TIMESTAMP(),
        existing_nullable=True,
    )
    op.drop_column("portfolio_companies", "updated_at")

    op.alter_column(
        "investors",
        "created_at",
        existing_type=sa.DateTime(timezone=True),
        type_=postgresql.TIMESTAMP(),
        existing_nullable=True,
    )
    op.drop_column("investors", "updated_at")

    op.drop_constraint("fk_investor_chunks_investor_id", "investor_chunks", type_="foreignkey")
    op.create_foreign_key("investor_chunks_investor_id_fkey", "investor_chunks", "investors", ["investor_id"], ["id"])
    op.alter_column(
        "investor_chunks",
        "created_at",
        existing_type=sa.DateTime(timezone=True),
        type_=postgresql.TIMESTAMP(),
        existing_nullable=True,
    )
    op.drop_column("investor_chunks", "updated_at")

    # Drop users table last since other tables depend on it
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_index(op.f("ix_users_clerk_id"), table_name="users")
    op.drop_table("users")
