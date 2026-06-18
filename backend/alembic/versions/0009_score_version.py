"""Scoring: score_version for auditability

Revision ID: 0009_score_version
Revises: 0008_session_fast_flag
Create Date: 2026-06-18 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0009_score_version"
down_revision: Union[str, None] = "0008_session_fast_flag"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("individual_scores", sa.Column("score_version", sa.String(20), nullable=True))


def downgrade() -> None:
    op.drop_column("individual_scores", "score_version")
