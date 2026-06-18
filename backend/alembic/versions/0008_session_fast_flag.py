"""Survey: bot/low-effort completion flag on sessions

Revision ID: 0008_session_fast_flag
Revises: 0007_question_conditions
Create Date: 2026-06-18 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0008_session_fast_flag"
down_revision: Union[str, None] = "0007_question_conditions"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "respondent_sessions",
        sa.Column("flagged_fast", sa.Boolean(), nullable=False, server_default="false"),
    )


def downgrade() -> None:
    op.drop_column("respondent_sessions", "flagged_fast")
