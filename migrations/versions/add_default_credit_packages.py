"""Add default credit packages.

Revision ID: add_default_credit_packages
Revises: d1b7e45b1fc7
Create Date: 2024-02-14 20:04:00.000000

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'add_default_credit_packages'
down_revision: Union[str, None] = 'add_currency_to_credit_packages'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Insert default credit packages
    op.execute(
        """
        INSERT INTO credit_packages (id, name, credits, price_cents, currency, tier, savings_percentage, is_active)
        VALUES
            -- USD Packages
            (gen_random_uuid(), 'Starter Pack (USD)', 100, 500, 'usd', 'basic', 0, true),
            (gen_random_uuid(), 'Pro Pack (USD)', 500, 2000, 'usd', 'pro', 20, true),
            (gen_random_uuid(), 'Business Pack (USD)', 2000, 7000, 'usd', 'business', 30, true),
            (gen_random_uuid(), 'Enterprise Pack (USD)', 5000, 15000, 'usd', 'enterprise', 40, true),
            -- EUR Packages (converted at approximate rate of 1 USD = 0.93 EUR)
            (gen_random_uuid(), 'Starter Pack (EUR)', 100, 465, 'eur', 'basic', 0, true),
            (gen_random_uuid(), 'Pro Pack (EUR)', 500, 1860, 'eur', 'pro', 20, true),
            (gen_random_uuid(), 'Business Pack (EUR)', 2000, 6510, 'eur', 'business', 30, true),
            (gen_random_uuid(), 'Enterprise Pack (EUR)', 5000, 13950, 'eur', 'enterprise', 40, true)
        """
    )


def downgrade() -> None:
    op.execute("DELETE FROM credit_packages")
