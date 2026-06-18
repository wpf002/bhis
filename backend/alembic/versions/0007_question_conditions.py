"""Survey: skip-logic foundation (question_conditions)

Revision ID: 0007_question_conditions
Revises: 0006_church_soft_delete
Create Date: 2026-06-18 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0007_question_conditions"
down_revision: Union[str, None] = "0006_church_soft_delete"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "question_conditions",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("question_id", sa.String(), nullable=False),
        sa.Column("depends_on_question_id", sa.String(), nullable=False),
        sa.Column("operator", sa.String(20), nullable=False, server_default="equals"),
        sa.Column("value", sa.String(255), nullable=True),
        sa.Column("action", sa.String(20), nullable=False, server_default="show"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["question_id"], ["questions.id"]),
        sa.ForeignKeyConstraint(["depends_on_question_id"], ["questions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_question_conditions_question_id", "question_conditions", ["question_id"])


def downgrade() -> None:
    op.drop_index("ix_question_conditions_question_id", table_name="question_conditions")
    op.drop_table("question_conditions")
