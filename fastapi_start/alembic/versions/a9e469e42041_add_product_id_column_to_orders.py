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
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    # Create products table if it does not exist (baseline support for fresh DBs)
    if not inspector.has_table("products"):
        op.create_table(
            "products",
            sa.Column("id", sa.Integer(), primary_key=True, index=True),
            sa.Column("name", sa.String(), nullable=True),
            sa.Column("price", sa.Float(), nullable=True),
            sa.Column("category", sa.String(), nullable=True),
            sa.Column("image", sa.String(), nullable=True),
        )

    # Create orders table if it does not exist (with legacy schema)
    if not inspector.has_table("orders"):
        op.create_table(
            "orders",
            sa.Column("id", sa.Integer(), primary_key=True, index=True),
            sa.Column("amount", sa.Float(), nullable=True),
            sa.Column("product_id", sa.Integer(), nullable=True),
            sa.Column("product_name", sa.String(), nullable=True),
            sa.Column("status", sa.String(), nullable=True, server_default="pending"),
        )
        return

    # If orders table exists, add the column when missing
    columns = {col["name"] for col in inspector.get_columns("orders")}
    if "product_id" not in columns:
        op.add_column("orders", sa.Column("product_id", sa.Integer(), nullable=True))

def downgrade():
    op.drop_column('orders', 'product_id')

