"""Widen questions.question_type to fit 'forced_prioritization' (21 chars)

Revision ID: 0010_widen_question_type
Revises: 0009_score_version
Create Date: 2026-06-18 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0010_widen_question_type"
down_revision: Union[str, None] = "0009_score_version"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("questions", "question_type", existing_type=sa.String(20), type_=sa.String(30))


def downgrade() -> None:
    op.alter_column("questions", "question_type", existing_type=sa.String(30), type_=sa.String(20))
