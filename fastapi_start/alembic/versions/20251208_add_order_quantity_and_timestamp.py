"""Add quantity and created_at to orders, remove product_name

Revision ID: add_quantity_and_timestamp
Revises: add_product_id_orders
Create Date: 2025-12-08
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "add_quantity_and_timestamp"
down_revision = "add_product_id_orders"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("orders") as batch_op:
        batch_op.add_column(
            sa.Column("quantity", sa.Integer(), nullable=False, server_default="1")
        )
        batch_op.add_column(
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("CURRENT_TIMESTAMP"),
            )
        )
        batch_op.drop_column("product_name")


def downgrade() -> None:
    with op.batch_alter_table("orders") as batch_op:
        batch_op.add_column(sa.Column("product_name", sa.String(), nullable=True))
        batch_op.drop_column("created_at")
        batch_op.drop_column("quantity")

