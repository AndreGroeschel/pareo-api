"""Add name field and make company_name optional in billing_info

Revision ID: add_name_to_billing_info
Revises: add_updated_at_to_invoices
Create Date: 2024-02-16 13:25

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'add_name_to_billing_info'
down_revision: Union[str, None] = 'add_updated_at_to_invoices'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add name column
    op.add_column('billing_info', sa.Column('name', sa.String(length=255), nullable=True))

    # Copy company_name to name for existing records
    op.execute("UPDATE billing_info SET name = company_name")

    # Make name not nullable after populating it
    op.alter_column('billing_info', 'name',
                    existing_type=sa.String(length=255),
                    nullable=False)

    # Make company_name nullable
    op.alter_column('billing_info', 'company_name',
                    existing_type=sa.String(length=255),
                    nullable=True)


def downgrade() -> None:
    # Copy name back to company_name for any null company_names
    op.execute("UPDATE billing_info SET company_name = name WHERE company_name IS NULL")

    # Make company_name not nullable again
    op.alter_column('billing_info', 'company_name',
                    existing_type=sa.String(length=255),
                    nullable=False)

    # Drop name column
    op.drop_column('billing_info', 'name')
