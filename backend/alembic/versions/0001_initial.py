"""Initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "churches",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("denomination", sa.String(100), nullable=True),
        sa.Column("size_range", sa.String(50), nullable=True),
        sa.Column("city", sa.String(100), nullable=True),
        sa.Column("state", sa.String(50), nullable=True),
        sa.Column("country", sa.String(50), nullable=True, server_default="US"),
        sa.Column("timezone", sa.String(50), nullable=True, server_default="America/Chicago"),
        sa.Column("theological_profile", sa.String(50), nullable=True),
        sa.Column("onboarding_complete", sa.Boolean(), nullable=True, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "users",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("church_id", sa.String(), nullable=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=True),
        sa.Column("first_name", sa.String(100), nullable=True),
        sa.Column("last_name", sa.String(100), nullable=True),
        sa.Column("role", sa.String(50), nullable=False, server_default="respondent"),
        sa.Column("is_active", sa.Boolean(), nullable=True, server_default="true"),
        sa.Column("email_verified", sa.Boolean(), nullable=True, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["church_id"], ["churches.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )

    op.create_table(
        "survey_templates",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("version", sa.String(20), nullable=False, server_default="1.0"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("question_count", sa.Integer(), nullable=True),
        sa.Column("estimated_minutes", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "survey_instances",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("church_id", sa.String(), nullable=False),
        sa.Column("template_id", sa.String(), nullable=False),
        sa.Column("assessment_cycle", sa.String(50), nullable=True),
        sa.Column("launch_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("close_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(20), nullable=True, server_default="draft"),
        sa.Column("respondent_count", sa.Integer(), nullable=True, server_default="0"),
        sa.Column("created_by", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["church_id"], ["churches.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["template_id"], ["survey_templates.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "questions",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("template_id", sa.String(), nullable=False),
        sa.Column("question_number", sa.Integer(), nullable=False),
        sa.Column("pillar", sa.String(50), nullable=False),
        sa.Column("question_text", sa.Text(), nullable=False),
        sa.Column("question_type", sa.String(20), nullable=False),
        sa.Column("is_contradiction_check", sa.Boolean(), nullable=True, server_default="false"),
        sa.Column("contradiction_pair_number", sa.Integer(), nullable=True),
        sa.Column("church_level_significance", sa.Boolean(), nullable=True, server_default="false"),
        sa.Column("individual_level_significance", sa.Boolean(), nullable=True, server_default="false"),
        sa.Column("scoring_weight", sa.Float(), nullable=True, server_default="1.0"),
        sa.Column("qualitative_only", sa.Boolean(), nullable=True, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["template_id"], ["survey_templates.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "question_options",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("question_id", sa.String(), nullable=False),
        sa.Column("option_letter", sa.String(1), nullable=False),
        sa.Column("option_text", sa.Text(), nullable=False),
        sa.Column("score_value", sa.Integer(), nullable=False),
        sa.Column("is_correct_answer", sa.Boolean(), nullable=True, server_default="false"),
        sa.Column("drift_signal", sa.Boolean(), nullable=True, server_default="false"),
        sa.Column("contradiction_trigger", sa.Boolean(), nullable=True, server_default="false"),
        sa.ForeignKeyConstraint(["question_id"], ["questions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "respondent_sessions",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("survey_instance_id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=True),
        sa.Column("anonymous_token", sa.String(255), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completion_time_seconds", sa.Integer(), nullable=True),
        sa.Column("is_complete", sa.Boolean(), nullable=True, server_default="false"),
        sa.ForeignKeyConstraint(["survey_instance_id"], ["survey_instances.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "responses",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("session_id", sa.String(), nullable=False),
        sa.Column("question_id", sa.String(), nullable=False),
        sa.Column("selected_option_id", sa.String(), nullable=True),
        sa.Column("likert_value", sa.Integer(), nullable=True),
        sa.Column("text_response", sa.Text(), nullable=True),
        sa.Column("ranking_order", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("response_time_seconds", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["question_id"], ["questions.id"]),
        sa.ForeignKeyConstraint(["selected_option_id"], ["question_options.id"]),
        sa.ForeignKeyConstraint(["session_id"], ["respondent_sessions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "individual_scores",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("session_id", sa.String(), nullable=False),
        sa.Column("composite_score", sa.Float(), nullable=True),
        sa.Column("maturity_tier", sa.String(50), nullable=True),
        sa.Column("contradiction_count", sa.Integer(), nullable=True, server_default="0"),
        sa.Column("credibility_warning", sa.Boolean(), nullable=True, server_default="false"),
        sa.Column("drift_risk_level", sa.String(20), nullable=True),
        sa.Column("drift_signal_count", sa.Integer(), nullable=True, server_default="0"),
        sa.Column("calculated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["session_id"], ["respondent_sessions.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("session_id"),
    )

    op.create_table(
        "pillar_scores",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("individual_score_id", sa.String(), nullable=False),
        sa.Column("pillar", sa.String(50), nullable=False),
        sa.Column("raw_score", sa.Float(), nullable=True),
        sa.Column("normalized_score", sa.Float(), nullable=True),
        sa.Column("question_count", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(20), nullable=True),
        sa.ForeignKeyConstraint(["individual_score_id"], ["individual_scores.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "contradiction_flags",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("individual_score_id", sa.String(), nullable=False),
        sa.Column("pair_id", sa.String(10), nullable=False),
        sa.Column("question_a_number", sa.Integer(), nullable=True),
        sa.Column("question_b_number", sa.Integer(), nullable=True),
        sa.Column("score_a", sa.Float(), nullable=True),
        sa.Column("score_b", sa.Float(), nullable=True),
        sa.Column("delta", sa.Float(), nullable=True),
        sa.Column("flagged", sa.Boolean(), nullable=True, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["individual_score_id"], ["individual_scores.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "church_aggregate_scores",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("survey_instance_id", sa.String(), nullable=False),
        sa.Column("church_id", sa.String(), nullable=False),
        sa.Column("health_score", sa.Float(), nullable=True),
        sa.Column("respondent_count", sa.Integer(), nullable=True),
        sa.Column("archetype", sa.String(100), nullable=True),
        sa.Column("drift_risk_score", sa.Float(), nullable=True),
        sa.Column("drift_risk_level", sa.String(20), nullable=True),
        sa.Column("maturity_distribution", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("pillar_scores", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("calculated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["church_id"], ["churches.id"]),
        sa.ForeignKeyConstraint(["survey_instance_id"], ["survey_instances.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("survey_instance_id"),
    )

    op.create_table(
        "recommendations",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("scope", sa.String(20), nullable=False),
        sa.Column("trigger_pillar", sa.String(50), nullable=True),
        sa.Column("trigger_condition", sa.String(100), nullable=True),
        sa.Column("priority", sa.Integer(), nullable=True),
        sa.Column("title", sa.String(255), nullable=True),
        sa.Column("diagnosis", sa.Text(), nullable=True),
        sa.Column("root_cause", sa.Text(), nullable=True),
        sa.Column("biblical_anchor", sa.Text(), nullable=True),
        sa.Column("intervention", sa.Text(), nullable=True),
        sa.Column("reassessment_timeline", sa.String(50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
    )

    # Indexes
    op.create_index("ix_users_email", "users", ["email"])
    op.create_index("ix_questions_template_number", "questions", ["template_id", "question_number"])
    op.create_index("ix_responses_session", "responses", ["session_id"])
    op.create_index("ix_individual_scores_session", "individual_scores", ["session_id"])
    op.create_index("ix_pillar_scores_individual", "pillar_scores", ["individual_score_id"])
    op.create_index("ix_church_scores_church", "church_aggregate_scores", ["church_id"])


def downgrade() -> None:
    op.drop_table("recommendations")
    op.drop_table("church_aggregate_scores")
    op.drop_table("contradiction_flags")
    op.drop_table("pillar_scores")
    op.drop_table("individual_scores")
    op.drop_table("responses")
    op.drop_table("respondent_sessions")
    op.drop_table("question_options")
    op.drop_table("questions")
    op.drop_table("survey_instances")
    op.drop_table("survey_templates")
    op.drop_table("users")
    op.drop_table("churches")
