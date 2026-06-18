"""Church invites: invite-based onboarding

Revision ID: 0005_church_invites
Revises: 0004_refresh_tokens
Create Date: 2026-06-18 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0005_church_invites"
down_revision: Union[str, None] = "0004_refresh_tokens"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "church_invites",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("church_id", sa.String(), nullable=False),
        sa.Column("role", sa.String(50), nullable=False, server_default="leader"),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["church_id"], ["churches.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_church_invites_church_id", "church_invites", ["church_id"])
    op.create_index("ix_church_invites_token_hash", "church_invites", ["token_hash"])


def downgrade() -> None:
    op.drop_index("ix_church_invites_token_hash", table_name="church_invites")
    op.drop_index("ix_church_invites_church_id", table_name="church_invites")
    op.drop_table("church_invites")
