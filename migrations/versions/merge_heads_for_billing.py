"""Merge multiple heads for billing

Revision ID: merge_heads_for_billing
Revises: add_name_to_billing_info, add_billing_info_table, 3daf0fe01f2e, simplify_credit_invoices
Create Date: 2024-02-16 13:28

"""
from typing import Sequence, Union



# revision identifiers, used by Alembic.
revision: str = 'merge_heads_for_billing'
down_revision = ('add_name_to_billing_info', 'add_billing_info_table')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
