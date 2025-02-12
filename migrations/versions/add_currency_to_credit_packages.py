"""Add currency column to credit packages.

Revision ID: add_currency_to_credit_packages
Revises: add_default_credit_packages
Create Date: 2024-02-14 22:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'add_currency_to_credit_packages'
down_revision: Union[str, None] = 'd1b7e45b1fc7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add currency column with default value
    op.add_column('credit_packages', sa.Column('currency', sa.String(3), nullable=False, server_default='usd'))

    # Update existing packages to use USD
    op.execute("""
        UPDATE credit_packages
        SET currency = 'usd'
        WHERE currency = 'usd'
    """)


def downgrade() -> None:
    op.drop_column('credit_packages', 'currency')
