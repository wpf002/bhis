import axios from 'axios'
import type {
  LoginPayload, RegisterPayload, TokenResponse,
  Church, ChurchDashboard, SurveyInstance, Question,
  ResponseEntry, IndividualReport, ChurchReport,
} from '../types'

const api = axios.create({
  baseURL: '/api/v1',
  headers: { 'Content-Type': 'application/json' },
})

// Attach token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// Auto-refresh on 401
api.interceptors.response.use(
  (r) => r,
  async (error) => {
    if (error.response?.status === 401) {
      const refresh = localStorage.getItem('refresh_token')
      if (refresh) {
        try {
          const { data } = await axios.post<TokenResponse>('/api/v1/auth/refresh', { refresh_token: refresh })
          localStorage.setItem('access_token', data.access_token)
          localStorage.setItem('refresh_token', data.refresh_token)
          error.config.headers.Authorization = `Bearer ${data.access_token}`
          return api(error.config)
        } catch {
          localStorage.clear()
          window.location.href = '/login'
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
  refresh: (refresh_token: string) => api.post<TokenResponse>('/auth/refresh', { refresh_token }).then(r => r.data),
}

// ── Churches ──────────────────────────────────────────────────────────────────

export const churchApi = {
  get: (id: string) => api.get<Church>(`/churches/${id}`).then(r => r.data),
  getDashboard: (id: string) => api.get<ChurchDashboard>(`/churches/${id}/dashboard`).then(r => r.data),
  create: (payload: Partial<Church>) => api.post<Church>('/churches', payload).then(r => r.data),
}

// ── Surveys ───────────────────────────────────────────────────────────────────

export const surveyApi = {
  getTemplates: () => api.get('/surveys/templates').then(r => r.data),
  createInstance: (payload: { template_id: string; assessment_cycle: string }) =>
    api.post<SurveyInstance>('/surveys/instances', payload).then(r => r.data),
  launch: (instanceId: string) =>
    api.post<SurveyInstance>(`/surveys/instances/${instanceId}/launch`).then(r => r.data),
  getQuestions: (instanceId: string) =>
    api.get<Question[]>(`/surveys/instances/${instanceId}/questions`).then(r => r.data),
}

// ── Responses ─────────────────────────────────────────────────────────────────

export const responseApi = {
  startSession: (surveyInstanceId: string) =>
    api.post('/responses/sessions', { survey_instance_id: surveyInstanceId }).then(r => r.data),
  submitResponses: (sessionId: string, responses: ResponseEntry[]) =>
    api.put(`/responses/sessions/${sessionId}`, { responses }).then(r => r.data),
  completeSession: (sessionId: string) =>
    api.post(`/responses/sessions/${sessionId}/complete`).then(r => r.data),
}

// ── Scoring ───────────────────────────────────────────────────────────────────

export const scoringApi = {
  scoreIndividual: (sessionId: string) =>
    api.post(`/scoring/individual/${sessionId}`).then(r => r.data),
  aggregateChurch: (instanceId: string) =>
    api.post(`/scoring/church/${instanceId}`).then(r => r.data),
}

// ── Reports ───────────────────────────────────────────────────────────────────

export const reportApi = {
  individual: (sessionId: string) =>
    api.get<IndividualReport>(`/reports/individual/${sessionId}`).then(r => r.data),
  church: (instanceId: string) =>
    api.get<ChurchReport>(`/reports/church/${instanceId}`).then(r => r.data),
}

export default api
