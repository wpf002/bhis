import { describe, it, expect, beforeEach } from 'vitest'
import {
  saveSurvey, loadSurvey, saveAnswers, clearSurvey,
  rememberReportToken, lastReportToken,
} from './surveySession'

const base = {
  instanceId: 'inst-1',
  sessionId: 'sess-1',
  token: 'cap-token-1',
  answers: {},
  updatedAt: 0,
}

describe('surveySession', () => {
  beforeEach(() => localStorage.clear())

  it('round-trips a saved survey', () => {
    saveSurvey(base)
    const loaded = loadSurvey('inst-1')
    expect(loaded?.sessionId).toBe('sess-1')
    expect(loaded?.token).toBe('cap-token-1')
  })

  it('returns null for an unknown instance', () => {
    expect(loadSurvey('missing')).toBeNull()
  })

  it('saveAnswers merges into an existing survey only', () => {
    saveSurvey(base)
    saveAnswers('inst-1', { q1: { question_id: 'q1', likert_value: 4 } })
    expect(loadSurvey('inst-1')?.answers.q1.likert_value).toBe(4)

    // no-op when there is no stored survey
    saveAnswers('inst-2', { q1: { question_id: 'q1', likert_value: 1 } })
    expect(loadSurvey('inst-2')).toBeNull()
  })

  it('clearSurvey removes it', () => {
    saveSurvey(base)
    clearSurvey('inst-1')
    expect(loadSurvey('inst-1')).toBeNull()
  })

  it('remembers the last report token', () => {
    expect(lastReportToken()).toBeNull()
    rememberReportToken('tok-xyz')
    expect(lastReportToken()).toBe('tok-xyz')
  })

  it('tolerates corrupt storage', () => {
    localStorage.setItem('bhis.survey.broken', '{not json')
    expect(loadSurvey('broken')).toBeNull()
  })
})
