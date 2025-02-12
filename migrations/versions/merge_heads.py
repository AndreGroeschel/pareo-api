"""Merge heads.

Revision ID: merge_heads
Revises: add_currency_to_credit_packages, add_deleted_at_to_users
Create Date: 2024-02-14 23:13:00.000000

"""
from typing import Sequence, Union


# revision identifiers, used by Alembic.
revision: str = 'merge_heads'
down_revision: Union[str, None] = ('add_currency_to_credit_packages', 'add_deleted_at_to_users')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
