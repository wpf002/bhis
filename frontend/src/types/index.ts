// ── Auth ──────────────────────────────────────────────────────────────────────

export interface AuthState {
  accessToken: string | null
  refreshToken: string | null
  userId: string | null
  role: 'respondent' | 'leader' | 'admin' | 'consultant' | null
}

export interface LoginPayload {
  email: string
  password: string
}

export interface RegisterPayload {
  email: string
  password: string
  first_name: string
  last_name: string
  role?: string
  church_id?: string
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
  user_id: string
  role: string
}

// ── Church ────────────────────────────────────────────────────────────────────

export interface Church {
  id: string
  name: string
  denomination?: string
  size_range?: string
  city?: string
  state?: string
  onboarding_complete: boolean
  created_at: string
}

export interface ChurchDashboard {
  church: Church
  health_score: number | null
  archetype: string | null
  drift_risk_level: 'low' | 'moderate' | 'high' | 'critical' | null
  drift_risk_score: number | null
  respondent_count: number | null
  maturity_distribution: Record<string, number> | null
  pillar_scores: Record<string, number> | null
  latest_cycle?: string
}

// ── Survey ────────────────────────────────────────────────────────────────────

export type QuestionType = 'likert' | 'mc' | 'behavioral_frequency' | 'scenario' | 'forced_prioritization' | 'open_ended'

export type Pillar =
  | 'doctrinal_integrity'
  | 'spiritual_discipline'
  | 'transformation_fruit'
  | 'discipleship_depth'
  | 'church_health_trust'
  | 'engagement_alignment'
  | 'drift_vulnerability'

export interface QuestionOption {
  id: string
  option_letter: string
  option_text: string
}

export interface Question {
  id: string
  question_number: number
  pillar: Pillar
  question_text: string
  question_type: QuestionType
  qualitative_only: boolean
  options: QuestionOption[]
}

export interface SurveyInstance {
  id: string
  church_id: string
  assessment_cycle: string
  status: 'draft' | 'active' | 'closed' | 'archived'
  respondent_count: number
  launch_date?: string
  close_date?: string
}

// ── Responses ─────────────────────────────────────────────────────────────────

export interface ResponseEntry {
  question_id: string
  selected_option_id?: string
  likert_value?: number
  text_response?: string
  ranking_order?: string[]
  response_time_seconds?: number
}

// ── Scores ────────────────────────────────────────────────────────────────────

export type MaturityTier =
  | 'Spiritually Disengaged'
  | 'Nominal'
  | 'Growing'
  | 'Grounded'
  | 'Multiplying Disciple'

export type DriftRisk = 'low' | 'moderate' | 'high' | 'critical'

export interface PillarScore {
  pillar: Pillar
  normalized_score: number
  status: 'strength' | 'moderate' | 'gap' | 'significant_gap'
}

export interface IndividualReport {
  composite_score: number
  maturity_tier: MaturityTier
  contradiction_count: number
  credibility_warning: boolean
  drift_risk_level: DriftRisk
  pillar_scores: Record<string, number>
  pillar_statuses: Record<string, string>
  recommendations: Recommendation[]
}

export interface ChurchReport {
  health_score: number
  archetype: string
  respondent_count: number
  drift_risk_level: DriftRisk
  drift_risk_score: number
  maturity_distribution: Record<string, number>
  pillar_scores: Record<string, number>
  recommendations: Recommendation[]
}

export interface Recommendation {
  priority: number
  pillar: string
  title: string
  urgency: 'HIGH' | 'MEDIUM' | 'LOW'
  diagnosis: string
  biblical_anchor: string
  intervention: string
  timeline: string
}

// ── UI helpers ────────────────────────────────────────────────────────────────

export const PILLAR_LABELS: Record<string, string> = {
  doctrinal_integrity: 'Doctrinal Integrity',
  spiritual_discipline: 'Spiritual Discipline',
  transformation_fruit: 'Transformation & Fruit',
  discipleship_depth: 'Discipleship Depth',
  church_health_trust: 'Church Health & Trust',
  engagement_alignment: 'Engagement & Alignment',
  drift_vulnerability: 'Drift & Vulnerability',
}

export const PILLAR_COLORS: Record<string, string> = {
  doctrinal_integrity: '#4B7BEC',
  spiritual_discipline: '#A55EEA',
  transformation_fruit: '#26DE81',
  discipleship_depth: '#FD9644',
  church_health_trust: '#2BCBBA',
  engagement_alignment: '#FC5C65',
  drift_vulnerability: '#F7B731',
}

export const MATURITY_TIER_COLORS: Record<MaturityTier, string> = {
  'Spiritually Disengaged': '#FC5C65',
  'Nominal': '#FD9644',
  'Growing': '#F7B731',
  'Grounded': '#26DE81',
  'Multiplying Disciple': '#4B7BEC',
}
