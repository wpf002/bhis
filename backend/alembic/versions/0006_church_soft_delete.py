"""Churches: soft-delete flag

Revision ID: 0006_church_soft_delete
Revises: 0005_church_invites
Create Date: 2026-06-18 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0006_church_soft_delete"
down_revision: Union[str, None] = "0005_church_invites"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "churches",
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
    )


def downgrade() -> None:
    op.drop_column("churches", "is_active")
