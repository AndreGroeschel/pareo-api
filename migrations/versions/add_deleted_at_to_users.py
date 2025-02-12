"""Add deleted_at column to users table

Revision ID: add_deleted_at_to_users
Revises: d1b7e45b1fc7
Create Date: 2025-02-12 00:30:47.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "add_deleted_at_to_users"
down_revision: Union[str, None] = "d1b7e45b1fc7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "deleted_at")
