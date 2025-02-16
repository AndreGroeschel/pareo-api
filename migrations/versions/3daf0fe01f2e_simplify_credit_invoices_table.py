"""simplify_credit_invoices_table

Revision ID: 3daf0fe01f2e
Revises: simplify_credit_invoices
Create Date: 2025-02-15 23:11:55.085036

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3daf0fe01f2e'
down_revision: Union[str, None] = '5a25238141f0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create unique constraint for existing stripe_invoice_id column
    op.create_unique_constraint('uq_credit_invoices_stripe_invoice_id', 'credit_invoices', ['stripe_invoice_id'])

    # Drop unnecessary columns
    op.drop_column('credit_invoices', 'amount_cents')
    op.drop_column('credit_invoices', 'currency')
    op.drop_column('credit_invoices', 'status')
    op.drop_column('credit_invoices', 'metadata')
    op.drop_column('credit_invoices', 'updated_at')

    # Make created_at nullable
    op.alter_column('credit_invoices', 'created_at',
                    existing_type=sa.DateTime(),
                    nullable=True,
                    server_default=None)


def downgrade() -> None:
    # Drop constraint only (don't drop the column since it was created in the initial migration)
    op.drop_constraint('uq_credit_invoices_stripe_invoice_id', 'credit_invoices', type_='unique')

    # Make created_at non-nullable with server default
    op.alter_column('credit_invoices', 'created_at',
                    existing_type=sa.DateTime(),
                    nullable=False,
                    server_default=sa.text('now()'))

    # Add back removed columns
    op.add_column('credit_invoices', sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False))
    op.add_column('credit_invoices', sa.Column('metadata', sa.JSON(), nullable=True))
    op.add_column('credit_invoices', sa.Column('status', sa.String(length=50), nullable=False))
    op.add_column('credit_invoices', sa.Column('currency', sa.String(), nullable=False))
    op.add_column('credit_invoices', sa.Column('amount_cents', sa.Integer(), nullable=False))
