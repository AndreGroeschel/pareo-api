"""Create credit configuration table

Revision ID: d1b7e45b1fc7
Revises: 8fc8eca45073
Create Date: 2025-02-10 22:53:22.918634

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd1b7e45b1fc7'
down_revision: Union[str, None] = '8fc8eca45073'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create credit_configurations table
    op.create_table(
        'credit_configurations',
        sa.Column('key', sa.String(100), primary_key=True),
        sa.Column('value', sa.Integer(), nullable=False),
        sa.Column('description', sa.String(255), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False)
    )

    # Insert initial configuration for signup bonus
    op.execute("""
        INSERT INTO credit_configurations (key, value, description)
        VALUES ('signup_bonus', 50, 'Number of credits awarded to new users upon signup')
    """)


def downgrade() -> None:
    # Remove the credit_configurations table
    op.drop_table('credit_configurations')
