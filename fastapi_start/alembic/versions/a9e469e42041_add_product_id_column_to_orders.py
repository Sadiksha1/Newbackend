"""Add product_id column to orders

Revision ID: a9e469e42041
Revises: 
Create Date: 2025-12-07 22:46:48.320626

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_product_id_orders'  # you can leave as-is
down_revision = None  # replace with your previous revision id if any
branch_labels = None
depends_on = None

def upgrade():
    # Add the new column WITHOUT foreign key constraint, but skip if it already exists
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {col["name"] for col in inspector.get_columns("orders")}
    if "product_id" not in columns:
        op.add_column('orders', sa.Column('product_id', sa.Integer(), nullable=True))

def downgrade():
    op.drop_column('orders', 'product_id')

