import type { ResponseEntry } from '../types'

/**
 * Local persistence for an in-progress (anonymous) survey.
 *
 * The capability token lives only on the member's device. We keep the session
 * id + token + answers in localStorage so a reload resumes where they left off
 * and so the report can be reached afterwards without a login.
 */
export interface StoredSurvey {
  instanceId: string
  sessionId: string
  token: string
  answers: Record<string, ResponseEntry>
  updatedAt: number
}

const keyFor = (instanceId: string) => `bhis.survey.${instanceId}`
const LAST_TOKEN_KEY = 'bhis.lastReportToken'

export function saveSurvey(s: StoredSurvey): void {
  localStorage.setItem(keyFor(s.instanceId), JSON.stringify({ ...s, updatedAt: Date.now() }))
}

export function loadSurvey(instanceId: string): StoredSurvey | null {
  const raw = localStorage.getItem(keyFor(instanceId))
  if (!raw) return null
  try {
    return JSON.parse(raw) as StoredSurvey
  } catch {
    return null
  }
}

export function saveAnswers(instanceId: string, answers: Record<string, ResponseEntry>): void {
  const existing = loadSurvey(instanceId)
  if (existing) saveSurvey({ ...existing, answers })
}

export function clearSurvey(instanceId: string): void {
  localStorage.removeItem(keyFor(instanceId))
}

/** Remember the capability token of the most recently completed survey so the
 *  member can return to their report. */
export function rememberReportToken(token: string): void {
  localStorage.setItem(LAST_TOKEN_KEY, token)
}

export function lastReportToken(): string | null {
  return localStorage.getItem(LAST_TOKEN_KEY)
}
