"""simplify_credit_invoices_table

Revision ID: simplify_credit_invoices
Revises: 5a25238141f0
Create Date: 2025-02-15 22:52:47.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'simplify_credit_invoices'
down_revision: Union[str, None] = '5a25238141f0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add stripe_invoice_id column first
    op.add_column('credit_invoices', sa.Column('stripe_invoice_id', sa.String(255), nullable=False))
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
    # Drop stripe_invoice_id column and its constraint
    op.drop_constraint('uq_credit_invoices_stripe_invoice_id', 'credit_invoices', type_='unique')
    op.drop_column('credit_invoices', 'stripe_invoice_id')

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
