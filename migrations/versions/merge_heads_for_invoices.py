"""merge heads for invoices

Revision ID: merge_heads_for_invoices
Revises: 3daf0fe01f2e, simplify_credit_invoices
Create Date: 2025-02-16 00:00:00.000000

"""
from typing import Sequence, Union



# revision identifiers, used by Alembic.
revision: str = 'merge_heads_for_invoices'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Update this to include all parent revisions
depends_on = ['3daf0fe01f2e', 'simplify_credit_invoices']


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
