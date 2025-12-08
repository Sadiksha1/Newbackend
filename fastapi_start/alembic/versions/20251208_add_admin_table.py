"""Create admins table for authenticated admin users

Revision ID: add_admin_table
Revises: add_quantity_and_timestamp
Create Date: 2025-12-08
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "add_admin_table"
down_revision = "add_quantity_and_timestamp"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "admins",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("username", sa.String(), nullable=False),
        sa.Column("password_hash", sa.String(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )
    op.create_index("ix_admins_username", "admins", ["username"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_admins_username", table_name="admins")
    op.drop_table("admins")

