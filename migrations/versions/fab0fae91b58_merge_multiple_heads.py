"""merge_multiple_heads

Revision ID: fab0fae91b58
Revises: add_default_credit_packages, merge_heads
Create Date: 2025-02-15 22:08:18.609052

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fab0fae91b58'
down_revision: Union[str, None] = ('add_default_credit_packages', 'merge_heads')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
