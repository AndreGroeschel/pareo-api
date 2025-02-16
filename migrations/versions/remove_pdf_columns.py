"""remove pdf columns

Revision ID: remove_pdf_columns
Revises: add_updated_at_to_invoices
Create Date: 2025-02-16 00:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'remove_pdf_columns'
down_revision: Union[str, None] = 'add_updated_at_to_invoices'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop pdf related columns
    op.drop_column('credit_invoices', 'pdf_generated')
    op.drop_column('credit_invoices', 'pdf_path')


def downgrade() -> None:
    # Add back pdf related columns
    op.add_column('credit_invoices', sa.Column('pdf_path', sa.String(255), nullable=True))
    op.add_column('credit_invoices', sa.Column('pdf_generated', sa.Boolean(), server_default=sa.text('false'), nullable=False))
