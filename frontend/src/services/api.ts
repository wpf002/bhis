import axios from 'axios'
import type {
  LoginPayload, RegisterPayload, TokenResponse,
  Church, ChurchDashboard, SurveyInstance, Question,
  ResponseEntry, IndividualReport, ChurchReport, SuppressedReport,
  SessionStartResponse, InstanceMeta, InviteResponse, ActiveSession, CurrentUser,
} from '../types'

const api = axios.create({
  baseURL: '/api/v1',
  headers: { 'Content-Type': 'application/json' },
})

// Attach access token to authenticated requests.
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// Rotate the refresh token on 401, then replay the original request once.
api.interceptors.response.use(
  (r) => r,
  async (error) => {
    const original = error.config
    if (error.response?.status === 401 && original && !original._retried) {
      const refresh = localStorage.getItem('refresh_token')
      if (refresh) {
        original._retried = true
        try {
          const { data } = await axios.post<TokenResponse>('/api/v1/auth/refresh', { refresh_token: refresh })
          localStorage.setItem('access_token', data.access_token)
          localStorage.setItem('refresh_token', data.refresh_token)
          original.headers.Authorization = `Bearer ${data.access_token}`
          return api(original)
        } catch {
          localStorage.clear()
          if (!window.location.pathname.startsWith('/login')) window.location.href = '/login'
        }
      }
    }
    return Promise.reject(error)
  }
)

// ── Auth ──────────────────────────────────────────────────────────────────────

export const authApi = {
  login: (payload: LoginPayload) => api.post<TokenResponse>('/auth/login', payload).then(r => r.data),
  register: (payload: RegisterPayload) => api.post<TokenResponse>('/auth/register', payload).then(r => r.data),
  registerViaInvite: (payload: { token: string; password: string; first_name: string; last_name: string; email?: string }) =>
    api.post<TokenResponse>('/auth/register-via-invite', payload).then(r => r.data),
  refresh: (refresh_token: string) => api.post<TokenResponse>('/auth/refresh', { refresh_token }).then(r => r.data),
  verifyEmail: (token: string) => api.post('/auth/verify-email', { token }).then(r => r.data),
  resendVerification: (email: string) => api.post('/auth/resend-verification', { email }).then(r => r.data),
  forgotPassword: (email: string) => api.post('/auth/forgot-password', { email }).then(r => r.data),
  resetPassword: (token: string, new_password: string) =>
    api.post('/auth/reset-password', { token, new_password }).then(r => r.data),
  logout: (refresh_token: string) => api.post('/auth/logout', { refresh_token }).then(r => r.data),
  listSessions: () => api.get<ActiveSession[]>('/auth/sessions').then(r => r.data),
  revokeAllSessions: () => api.post('/auth/sessions/revoke-all').then(r => r.data),
  me: () => api.get<CurrentUser>('/auth/me').then(r => r.data),
}

// ── Churches ──────────────────────────────────────────────────────────────────

export const churchApi = {
  get: (id: string) => api.get<Church>(`/churches/${id}`).then(r => r.data),
  getDashboard: (id: string) => api.get<ChurchDashboard>(`/churches/${id}/dashboard`).then(r => r.data),
  create: (payload: Partial<Church>) => api.post<Church>('/churches', payload).then(r => r.data),
  updateSettings: (id: string, payload: Partial<Church>) =>
    api.put<Church>(`/churches/${id}/settings`, payload).then(r => r.data),
  deactivate: (id: string) => api.delete(`/churches/${id}`).then(r => r.data),
  createInvite: (churchId: string, payload: { role?: string; email?: string; expires_in_days?: number }) =>
    api.post<InviteResponse>(`/churches/${churchId}/invites`, payload).then(r => r.data),
}

// ── Surveys ───────────────────────────────────────────────────────────────────

export const surveyApi = {
  getTemplates: () => api.get('/surveys/templates').then(r => r.data),
  createInstance: (payload: { template_id: string; assessment_cycle: string; close_date?: string }) =>
    api.post<SurveyInstance>('/surveys/instances', payload).then(r => r.data),
  launch: (instanceId: string) =>
    api.post<SurveyInstance>(`/surveys/instances/${instanceId}/launch`).then(r => r.data),
  close: (instanceId: string) =>
    api.post<SurveyInstance>(`/surveys/instances/${instanceId}/close`).then(r => r.data),
  getMeta: (instanceId: string) =>
    api.get<InstanceMeta>(`/surveys/instances/${instanceId}`).then(r => r.data),
  getQuestions: (instanceId: string) =>
    api.get<Question[]>(`/surveys/instances/${instanceId}/questions`).then(r => r.data),
}

// ── Responses (anonymous, capability-token authorized) ────────────────────────

export const responseApi = {
  startSession: (surveyInstanceId: string) =>
    api.post<SessionStartResponse>('/responses/sessions', { survey_instance_id: surveyInstanceId }).then(r => r.data),
  submitResponses: (sessionId: string, token: string, responses: ResponseEntry[]) =>
    api.put(`/responses/sessions/${sessionId}`, { responses }, { headers: { 'X-Session-Token': token } }).then(r => r.data),
  completeSession: (sessionId: string, token: string) =>
    api.post(`/responses/sessions/${sessionId}/complete`, null, { headers: { 'X-Session-Token': token } }).then(r => r.data),
}

// ── Scoring (manual triggers; completion auto-scores on the backend) ──────────

export const scoringApi = {
  scoreIndividual: (sessionId: string) =>
    api.post(`/scoring/individual/${sessionId}`).then(r => r.data),
  aggregateChurch: (instanceId: string) =>
    api.post(`/scoring/church/${instanceId}`).then(r => r.data),
}

// ── Reports ───────────────────────────────────────────────────────────────────

export const reportApi = {
  individualByToken: (token: string) =>
    api.get<IndividualReport>(`/reports/individual/by-token/${token}`).then(r => r.data),
  church: (instanceId: string) =>
    api.get<ChurchReport | SuppressedReport>(`/reports/church/${instanceId}`).then(r => r.data),
  deliver: (sessionToken: string, email: string) =>
    api.post('/reports/deliver', { session_token: sessionToken, email }).then(r => r.data),
  claim: (sessionToken: string) =>
    api.post('/reports/claim', { session_token: sessionToken }).then(r => r.data),
  mine: () => api.get('/reports/mine').then(r => r.data),
  // Export URLs are plain links the browser can open/download directly.
  individualExportUrl: (token: string, fmt: 'html' | 'pdf' = 'html') =>
    `/api/v1/reports/individual/by-token/${token}/export?fmt=${fmt}`,
  churchExportUrl: (instanceId: string, fmt: 'html' | 'pdf' = 'html') =>
    `/api/v1/reports/church/${instanceId}/export?fmt=${fmt}`,
}

export default api
