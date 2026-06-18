import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean, Column, DateTime, Float, ForeignKey,
    Integer, JSON, String, Text, func
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


def gen_uuid():
    return str(uuid.uuid4())


# ── Churches ──────────────────────────────────────────────────────────────────

class Church(Base):
    __tablename__ = "churches"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    name = Column(String(255), nullable=False)
    denomination = Column(String(100))
    size_range = Column(String(50))       # "100-250", "250-500", etc.
    city = Column(String(100))
    state = Column(String(50))
    country = Column(String(50), default="US")
    timezone = Column(String(50), default="America/Chicago")
    theological_profile = Column(String(50))  # "evangelical", "reformed", etc.
    onboarding_complete = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True, nullable=False)  # soft-delete flag
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    users = relationship("User", back_populates="church")
    survey_instances = relationship("SurveyInstance", back_populates="church")
    aggregate_scores = relationship("ChurchAggregateScore", back_populates="church")


# ── Users ─────────────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    church_id = Column(UUID(as_uuid=False), ForeignKey("churches.id"), nullable=True)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255))
    first_name = Column(String(100))
    last_name = Column(String(100))
    role = Column(String(50), nullable=False, default="respondent")
    # roles: respondent | leader | admin | consultant
    is_active = Column(Boolean, default=True)
    email_verified = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    church = relationship("Church", back_populates="users")
    # NOTE: no relationship to RespondentSession. Survey sessions are anonymous and
    # carry no user_id — a member retrieves their report via capability token, not
    # identity. Optional account linkage is an opaque keyring (UserReportToken).
    report_tokens = relationship("UserReportToken", back_populates="user")


# ── Survey Templates ──────────────────────────────────────────────────────────

class SurveyTemplate(Base):
    __tablename__ = "survey_templates"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    name = Column(String(255), nullable=False)
    version = Column(String(20), nullable=False, default="1.0")
    description = Column(Text)
    question_count = Column(Integer)
    estimated_minutes = Column(Integer)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    questions = relationship("Question", back_populates="template")
    instances = relationship("SurveyInstance", back_populates="template")


class SurveyInstance(Base):
    __tablename__ = "survey_instances"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    church_id = Column(UUID(as_uuid=False), ForeignKey("churches.id"), nullable=False)
    template_id = Column(UUID(as_uuid=False), ForeignKey("survey_templates.id"), nullable=False)
    assessment_cycle = Column(String(50))  # "Q1-2024"
    launch_date = Column(DateTime(timezone=True))
    close_date = Column(DateTime(timezone=True))
    status = Column(String(20), default="draft")  # draft | active | closed | archived
    respondent_count = Column(Integer, default=0)
    created_by = Column(UUID(as_uuid=False), ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    church = relationship("Church", back_populates="survey_instances")
    template = relationship("SurveyTemplate", back_populates="instances")
    sessions = relationship("RespondentSession", back_populates="survey_instance")
    aggregate_score = relationship("ChurchAggregateScore", back_populates="survey_instance", uselist=False)


# ── Questions ─────────────────────────────────────────────────────────────────

class Question(Base):
    __tablename__ = "questions"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    template_id = Column(UUID(as_uuid=False), ForeignKey("survey_templates.id"), nullable=False)
    question_number = Column(Integer, nullable=False)
    pillar = Column(String(50), nullable=False)
    # doctrinal_integrity | spiritual_discipline | transformation_fruit |
    # discipleship_depth | church_health_trust | engagement_alignment | drift_vulnerability
    question_text = Column(Text, nullable=False)
    question_type = Column(String(20), nullable=False)
    # likert | mc | behavioral_frequency | scenario | forced_prioritization | open_ended
    is_contradiction_check = Column(Boolean, default=False)
    contradiction_pair_number = Column(Integer, nullable=True)  # Q number of paired question
    church_level_significance = Column(Boolean, default=False)
    individual_level_significance = Column(Boolean, default=False)
    scoring_weight = Column(Float, default=1.0)
    qualitative_only = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    template = relationship("SurveyTemplate", back_populates="questions")
    options = relationship("QuestionOption", back_populates="question", order_by="QuestionOption.option_letter")
    responses = relationship("Response", back_populates="question")


class QuestionOption(Base):
    __tablename__ = "question_options"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    question_id = Column(UUID(as_uuid=False), ForeignKey("questions.id"), nullable=False)
    option_letter = Column(String(1), nullable=False)  # a, b, c, d, e
    option_text = Column(Text, nullable=False)
    score_value = Column(Integer, nullable=False)  # 0-100
    is_correct_answer = Column(Boolean, default=False)
    drift_signal = Column(Boolean, default=False)
    contradiction_trigger = Column(Boolean, default=False)

    question = relationship("Question", back_populates="options")


# ── Responses ─────────────────────────────────────────────────────────────────

class RespondentSession(Base):
    __tablename__ = "respondent_sessions"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    survey_instance_id = Column(UUID(as_uuid=False), ForeignKey("survey_instances.id"), nullable=False)
    # No user_id. Identity is severed from responses by design (see
    # docs/anonymity-design.md). The session is reached only via anonymous_token,
    # an unguessable capability the member holds and the church never sees.
    anonymous_token = Column(String(255), nullable=False, unique=True, index=True)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))
    completion_time_seconds = Column(Integer)
    is_complete = Column(Boolean, default=False)

    survey_instance = relationship("SurveyInstance", back_populates="sessions")
    responses = relationship("Response", back_populates="session")
    individual_score = relationship("IndividualScore", back_populates="session", uselist=False)


class Response(Base):
    __tablename__ = "responses"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    session_id = Column(UUID(as_uuid=False), ForeignKey("respondent_sessions.id"), nullable=False)
    question_id = Column(UUID(as_uuid=False), ForeignKey("questions.id"), nullable=False)
    selected_option_id = Column(UUID(as_uuid=False), ForeignKey("question_options.id"), nullable=True)
    likert_value = Column(Integer)  # 1-5
    text_response = Column(Text)
    ranking_order = Column(JSON)
    response_time_seconds = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    session = relationship("RespondentSession", back_populates="responses")
    question = relationship("Question", back_populates="responses")
    selected_option = relationship("QuestionOption")


# ── Scores ────────────────────────────────────────────────────────────────────

class IndividualScore(Base):
    __tablename__ = "individual_scores"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    session_id = Column(UUID(as_uuid=False), ForeignKey("respondent_sessions.id"), nullable=False, unique=True)
    composite_score = Column(Float)
    maturity_tier = Column(String(50))
    contradiction_count = Column(Integer, default=0)
    credibility_warning = Column(Boolean, default=False)
    drift_risk_level = Column(String(20))  # low | moderate | high | critical
    drift_signal_count = Column(Integer, default=0)
    calculated_at = Column(DateTime(timezone=True), server_default=func.now())

    session = relationship("RespondentSession", back_populates="individual_score")
    pillar_scores = relationship("PillarScore", back_populates="individual_score")
    contradiction_flags = relationship("ContradictionFlag", back_populates="individual_score")


class PillarScore(Base):
    __tablename__ = "pillar_scores"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    individual_score_id = Column(UUID(as_uuid=False), ForeignKey("individual_scores.id"), nullable=False)
    pillar = Column(String(50), nullable=False)
    raw_score = Column(Float)
    normalized_score = Column(Float)
    question_count = Column(Integer)
    status = Column(String(20))  # strength | moderate | gap | significant_gap

    individual_score = relationship("IndividualScore", back_populates="pillar_scores")


class ContradictionFlag(Base):
    __tablename__ = "contradiction_flags"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    individual_score_id = Column(UUID(as_uuid=False), ForeignKey("individual_scores.id"), nullable=False)
    pair_id = Column(String(10), nullable=False)  # CP-01, CP-02, etc.
    question_a_number = Column(Integer)
    question_b_number = Column(Integer)
    score_a = Column(Float)
    score_b = Column(Float)
    delta = Column(Float)
    flagged = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    individual_score = relationship("IndividualScore", back_populates="contradiction_flags")


class ChurchAggregateScore(Base):
    __tablename__ = "church_aggregate_scores"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    survey_instance_id = Column(UUID(as_uuid=False), ForeignKey("survey_instances.id"), nullable=False, unique=True)
    church_id = Column(UUID(as_uuid=False), ForeignKey("churches.id"), nullable=False)
    health_score = Column(Float)
    respondent_count = Column(Integer)
    archetype = Column(String(100))
    drift_risk_score = Column(Float)
    drift_risk_level = Column(String(20))
    maturity_distribution = Column(JSON)
    pillar_scores = Column(JSON)  # {pillar: score}
    calculated_at = Column(DateTime(timezone=True), server_default=func.now())

    survey_instance = relationship("SurveyInstance", back_populates="aggregate_score")
    church = relationship("Church", back_populates="aggregate_scores")


class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    scope = Column(String(20), nullable=False)       # individual | church
    trigger_pillar = Column(String(50))
    trigger_condition = Column(String(100))
    priority = Column(Integer)
    title = Column(String(255))
    diagnosis = Column(Text)
    root_cause = Column(Text)
    biblical_anchor = Column(Text)
    intervention = Column(Text)
    reassessment_timeline = Column(String(50))
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# ── Anonymity: report retrieval without re-identification ─────────────────────
# See docs/anonymity-design.md. Both tables are deliberately NOT linked to
# churches, and the email-delivery table is not linked to users either — there
# is no FK path a church admin could traverse from church_id to a respondent.

class ReportDelivery(Base):
    """Emailing a member their own report link, keyed only by the capability
    token. No church_id, no user_id — severed from any identity the church holds."""
    __tablename__ = "report_deliveries"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    session_token = Column(String(255), nullable=False, index=True)  # = RespondentSession.anonymous_token
    email = Column(String(255), nullable=False)  # member's own address, for sending only
    sent_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class UserReportToken(Base):
    """Optional post-survey account = a personal keyring of capability tokens.
    Keyed from the user side; row access is restricted to the owning user, so a
    church admin still cannot link any response to a member."""
    __tablename__ = "user_report_tokens"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False, index=True)
    session_token = Column(String(255), nullable=False)  # the capability the member already holds
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="report_tokens")


# ── Auth: single-use email/password tokens ────────────────────────────────────

class AuthToken(Base):
    """Single-use, purpose-scoped token for email verification and password
    reset. Only a SHA-256 hash of the token is stored, so a DB leak does not
    yield usable tokens."""
    __tablename__ = "auth_tokens"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False, index=True)
    purpose = Column(String(30), nullable=False)  # verify_email | reset_password
    token_hash = Column(String(64), nullable=False, index=True)  # sha256 hex
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class RefreshToken(Base):
    """One row per issued refresh token, tracked by jti so refresh rotation can
    invalidate the prior token and detect reuse of a rotated/stolen token."""
    __tablename__ = "refresh_tokens"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False, index=True)
    jti = Column(String(64), nullable=False, unique=True, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    revoked = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ChurchInvite(Base):
    """A single-use invite that lets someone register into a specific church with
    a preset role. Only the token hash is stored."""
    __tablename__ = "church_invites"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    church_id = Column(UUID(as_uuid=False), ForeignKey("churches.id"), nullable=False, index=True)
    role = Column(String(50), nullable=False, default="leader")
    email = Column(String(255))  # optional: pin the invite to a specific address
    token_hash = Column(String(64), nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used_at = Column(DateTime(timezone=True))
    created_by = Column(UUID(as_uuid=False), ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class QuestionCondition(Base):
    """Skip-logic foundation (Phase 6): show/hide a question based on a prior
    answer. Defined now so the schema is in place; not yet evaluated during
    serving."""
    __tablename__ = "question_conditions"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    question_id = Column(UUID(as_uuid=False), ForeignKey("questions.id"), nullable=False, index=True)
    depends_on_question_id = Column(UUID(as_uuid=False), ForeignKey("questions.id"), nullable=False)
    operator = Column(String(20), nullable=False, default="equals")  # equals|not_equals|gt|lt|in
    value = Column(String(255))  # option_letter or numeric threshold
    action = Column(String(20), nullable=False, default="show")  # show | hide
    created_at = Column(DateTime(timezone=True), server_default=func.now())
