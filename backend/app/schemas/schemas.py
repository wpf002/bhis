from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr


# ── Auth ──────────────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    church_id: Optional[str] = None
    role: str = "respondent"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user_id: str
    role: str


class RefreshRequest(BaseModel):
    refresh_token: str


# ── Churches ──────────────────────────────────────────────────────────────────

class ChurchCreate(BaseModel):
    name: str
    denomination: Optional[str] = None
    size_range: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    theological_profile: Optional[str] = None


class ChurchResponse(BaseModel):
    id: str
    name: str
    denomination: Optional[str]
    size_range: Optional[str]
    city: Optional[str]
    state: Optional[str]
    onboarding_complete: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ── Surveys ───────────────────────────────────────────────────────────────────

class SurveyInstanceCreate(BaseModel):
    template_id: str
    assessment_cycle: str
    close_date: Optional[datetime] = None


class SurveyInstanceResponse(BaseModel):
    id: str
    church_id: str
    assessment_cycle: str
    status: str
    respondent_count: int
    launch_date: Optional[datetime]
    close_date: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class QuestionOptionSchema(BaseModel):
    id: str
    option_letter: str
    option_text: str

    class Config:
        from_attributes = True


class QuestionSchema(BaseModel):
    id: str
    question_number: int
    pillar: str
    question_text: str
    question_type: str
    qualitative_only: bool
    options: List[QuestionOptionSchema]

    class Config:
        from_attributes = True


# ── Responses ─────────────────────────────────────────────────────────────────

class SessionStart(BaseModel):
    survey_instance_id: str


class SessionResponse(BaseModel):
    id: str
    survey_instance_id: str
    started_at: datetime
    is_complete: bool
    # The capability token is returned ONCE on session creation. The member keeps
    # it (bookmark / email / account keyring) to reach their report later. It is
    # never exposed to church roles.
    anonymous_token: str

    class Config:
        from_attributes = True


class ClaimReportRequest(BaseModel):
    """Attach a capability token to the logged-in user's personal keyring."""
    session_token: str


class ResponseSubmit(BaseModel):
    question_id: str
    selected_option_id: Optional[str] = None
    likert_value: Optional[int] = None
    text_response: Optional[str] = None
    ranking_order: Optional[List[str]] = None
    response_time_seconds: Optional[int] = None


class BulkResponseSubmit(BaseModel):
    responses: List[ResponseSubmit]


# ── Scores ────────────────────────────────────────────────────────────────────

class PillarScoreSchema(BaseModel):
    pillar: str
    normalized_score: float
    status: str

    class Config:
        from_attributes = True


class IndividualScoreSchema(BaseModel):
    id: str
    composite_score: float
    maturity_tier: str
    contradiction_count: int
    credibility_warning: bool
    drift_risk_level: str
    drift_signal_count: int
    pillar_scores: List[PillarScoreSchema]

    class Config:
        from_attributes = True


class ChurchDashboardSchema(BaseModel):
    church: ChurchResponse
    health_score: Optional[float]
    archetype: Optional[str]
    drift_risk_level: Optional[str]
    drift_risk_score: Optional[float]
    respondent_count: Optional[int]
    maturity_distribution: Optional[Dict[str, Any]]
    pillar_scores: Optional[Dict[str, float]]
    latest_cycle: Optional[str]
