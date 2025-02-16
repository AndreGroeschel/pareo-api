"""add updated_at to invoices

Revision ID: add_updated_at_to_invoices
Revises: 3daf0fe01f2e
Create Date: 2025-02-16 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_updated_at_to_invoices'
down_revision: Union[str, None] = 'merge_heads_for_invoices'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add updated_at column with server default
    op.add_column('credit_invoices', sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True))


def downgrade() -> None:
    # Drop updated_at column
    op.drop_column('credit_invoices', 'updated_at')
