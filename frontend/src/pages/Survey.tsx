import { useState, useEffect, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { surveyApi, responseApi } from '../services/api'
import type { Question, ResponseEntry } from '../types'
import { loadSurvey, saveSurvey, saveAnswers, clearSurvey, rememberReportToken } from '../lib/surveySession'
import { Logo } from '../components/ui'
import clsx from 'clsx'

type Phase = 'intro' | 'questions' | 'submitting' | 'done'

const OPTION_BASE = 'w-full text-left rounded-2xl border px-5 py-4 transition-all'
const OPTION_IDLE = 'bg-surface border-line text-ink-soft hover:border-sage/50 hover:text-ink'
const OPTION_ON = 'bg-sage-soft border-sage text-ink'

export default function SurveyPage() {
  const { instanceId } = useParams<{ instanceId: string }>()
  const navigate = useNavigate()

  const [phase, setPhase] = useState<Phase>('intro')
  const [session, setSession] = useState<{ id: string; token: string } | null>(null)
  const [currentIndex, setCurrentIndex] = useState(0)
  const [responses, setResponses] = useState<Record<string, ResponseEntry>>({})
  const [error, setError] = useState('')
  const startTime = useRef<number>(Date.now())

  const { data: questions = [], isLoading } = useQuery({
    queryKey: ['questions', instanceId],
    queryFn: () => surveyApi.getQuestions(instanceId!),
    enabled: !!instanceId && phase !== 'intro',
  })
  const { data: meta } = useQuery({
    queryKey: ['instanceMeta', instanceId],
    queryFn: () => surveyApi.getMeta(instanceId!),
    enabled: !!instanceId,
  })

  useEffect(() => {
    if (!instanceId) return
    const saved = loadSurvey(instanceId)
    if (saved) {
      setSession({ id: saved.sessionId, token: saved.token })
      setResponses(saved.answers || {})
      setPhase('questions')
    }
  }, [instanceId])

  useEffect(() => {
    if (phase !== 'questions') return
    const handler = (e: BeforeUnloadEvent) => { e.preventDefault(); e.returnValue = '' }
    window.addEventListener('beforeunload', handler)
    return () => window.removeEventListener('beforeunload', handler)
  }, [phase])

  const begin = async () => {
    if (!instanceId) return
    try {
      const s = await responseApi.startSession(instanceId)
      saveSurvey({ instanceId, sessionId: s.id, token: s.anonymous_token, answers: {}, updatedAt: Date.now() })
      setSession({ id: s.id, token: s.anonymous_token })
      setPhase('questions')
      startTime.current = Date.now()
    } catch {
      setError('This assessment isn’t open right now.')
    }
  }

  const currentQ: Question | undefined = questions[currentIndex]
  const progress = questions.length > 0 ? (currentIndex / questions.length) * 100 : 0
  const currentResponse = currentQ ? responses[currentQ.id] : undefined

  const record = (entry: Partial<ResponseEntry>) => {
    if (!currentQ || !instanceId) return
    const next = {
      ...responses,
      [currentQ.id]: { question_id: currentQ.id, response_time_seconds: Math.round((Date.now() - startTime.current) / 1000), ...entry },
    }
    setResponses(next)
    saveAnswers(instanceId, next)
    startTime.current = Date.now()
  }

  const toggleRank = (letter: string) => {
    if (!currentQ) return
    const current = currentResponse?.ranking_order || []
    const next = current.includes(letter) ? current.filter(l => l !== letter) : [...current, letter]
    record({ ranking_order: next })
  }

  const canAdvance = currentQ && (
    currentQ.question_type === 'open_ended' ||
    (currentQ.question_type === 'forced_prioritization'
      ? (currentResponse?.ranking_order?.length || 0) === currentQ.options.length
      : responses[currentQ.id] !== undefined)
  )

  const handleNext = () => {
    if (currentIndex < questions.length - 1) setCurrentIndex(i => i + 1)
    else handleSubmit()
  }

  const handleSubmit = async () => {
    if (!session || !instanceId) return
    setPhase('submitting'); setError('')
    try {
      await responseApi.submitResponses(session.id, session.token, Object.values(responses))
      await responseApi.completeSession(session.id, session.token)
      rememberReportToken(session.token)
      clearSurvey(instanceId)
      setPhase('done')
      setTimeout(() => navigate(`/report/${session.token}`), 1600)
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'Something went wrong. Please try again.')
      setPhase('questions')
    }
  }

  // ── Intro / consent ─────────────────────────────────────────────────────────
  if (phase === 'intro') {
    return (
      <div className="min-h-screen bg-canvas flex items-center justify-center px-6 py-12">
        <div className="w-full max-w-lg text-center animate-fade-up">
          <div className="flex justify-center mb-8"><Logo /></div>
          <h1 className="text-3xl text-ink mb-4">A few honest minutes</h1>
          <p className="text-ink-soft leading-relaxed mb-6">
            This reflection helps your church care for its people well. There are no right or wrong
            answers — just answer honestly. It takes about {meta?.estimated_minutes ?? 10}–{(meta?.estimated_minutes ?? 10) + 2} minutes
            {meta ? ` (${meta.question_count} questions)` : ''}.
          </p>
          <div className="card p-5 text-left mb-7">
            <div className="text-sm font-semibold text-sage-dark mb-1">Your answers are completely anonymous</div>
            <p className="text-sm text-ink-soft leading-relaxed">
              Your church only ever sees combined results — never your individual answers, and there’s no way
              to trace a response back to you. At the end, you’ll receive your own private reflection to keep.
            </p>
          </div>
          {error && <div className="text-clay text-sm mb-4">{error}</div>}
          <button onClick={begin} className="btn-primary px-8">Begin</button>
        </div>
      </div>
    )
  }

  if (phase === 'done') {
    return (
      <div className="min-h-screen bg-canvas flex items-center justify-center px-6">
        <div className="text-center animate-fade-up">
          <div className="w-14 h-14 rounded-full bg-sage-soft text-sage-dark text-2xl flex items-center justify-center mx-auto mb-4">✓</div>
          <div className="text-ink text-xl mb-1 font-serif">Thank you</div>
          <div className="text-ink-soft text-sm">Preparing your private reflection…</div>
        </div>
      </div>
    )
  }

  if (isLoading) {
    return <div className="min-h-screen bg-canvas flex items-center justify-center"><div className="text-ink-faint text-sm">Loading…</div></div>
  }

  return (
    <div className="min-h-screen bg-canvas flex flex-col">
      <header className="border-b border-line bg-surface/70 backdrop-blur px-6 py-4 sticky top-0">
        <div className="max-w-2xl mx-auto flex items-center justify-between">
          <Logo />
          <div className="text-sm text-ink-faint">Question {currentIndex + 1} of {questions.length}</div>
        </div>
        <div className="max-w-2xl mx-auto mt-3">
          <div className="h-1.5 bg-warmth rounded-full overflow-hidden" role="progressbar" aria-valuenow={Math.round(progress)} aria-valuemin={0} aria-valuemax={100}>
            <div className="h-full bg-sage rounded-full transition-all duration-500" style={{ width: `${progress}%` }} />
          </div>
        </div>
      </header>

      <div className="flex-1 flex items-center justify-center px-6 py-10">
        {currentQ && (
          <div key={currentIndex} className="w-full max-w-2xl animate-fade-up">
            <div className="eyebrow mb-4">{currentQ.pillar.replace(/_/g, ' ')}</div>
            <h2 className="text-2xl text-ink leading-snug mb-8">{currentQ.question_text}</h2>

            {currentQ.question_type === 'likert' && (
              <div className="space-y-2.5">
                {[[1, 'Strongly disagree'], [2, 'Disagree'], [3, 'Neutral'], [4, 'Agree'], [5, 'Strongly agree']].map(([val, label]) => (
                  <button key={val} onClick={() => record({ likert_value: Number(val) })}
                    className={clsx(OPTION_BASE, 'flex items-center gap-4', currentResponse?.likert_value === val ? OPTION_ON : OPTION_IDLE)}>
                    <span className={clsx('w-5 h-5 rounded-full border-2 flex items-center justify-center flex-shrink-0', currentResponse?.likert_value === val ? 'border-sage bg-sage' : 'border-line')}>
                      {currentResponse?.likert_value === val && <span className="w-2 h-2 rounded-full bg-white" />}
                    </span>
                    <span>{label as string}</span>
                  </button>
                ))}
              </div>
            )}

            {['mc', 'scenario', 'behavioral_frequency'].includes(currentQ.question_type) && (
              <div className="space-y-2.5">
                {currentQ.options.map(opt => (
                  <button key={opt.id} onClick={() => record({ selected_option_id: opt.id })}
                    className={clsx(OPTION_BASE, 'flex items-start gap-4', currentResponse?.selected_option_id === opt.id ? OPTION_ON : OPTION_IDLE)}>
                    <span className={clsx('text-xs font-semibold mt-0.5 flex-shrink-0 w-5', currentResponse?.selected_option_id === opt.id ? 'text-sage-dark' : 'text-ink-faint')}>{opt.option_letter.toUpperCase()}</span>
                    <span className="leading-relaxed">{opt.option_text}</span>
                  </button>
                ))}
              </div>
            )}

            {currentQ.question_type === 'forced_prioritization' && (
              <div className="space-y-2.5">
                <p className="text-sm text-ink-faint mb-3">Tap in order, from most to least important.</p>
                {currentQ.options.map(opt => {
                  const rank = (currentResponse?.ranking_order || []).indexOf(opt.option_letter)
                  return (
                    <button key={opt.id} onClick={() => toggleRank(opt.option_letter)}
                      className={clsx(OPTION_BASE, 'flex items-center gap-4', rank >= 0 ? OPTION_ON : OPTION_IDLE)}>
                      <span className={clsx('w-7 h-7 rounded-full flex items-center justify-center text-xs font-semibold flex-shrink-0', rank >= 0 ? 'bg-sage text-white' : 'border border-line text-ink-faint')}>{rank >= 0 ? rank + 1 : ''}</span>
                      <span className="leading-relaxed">{opt.option_text}</span>
                    </button>
                  )
                })}
              </div>
            )}

            {currentQ.question_type === 'open_ended' && (
              <div>
                <textarea value={currentResponse?.text_response || ''} onChange={e => record({ text_response: e.target.value })}
                  placeholder="Share as much or as little as you like… (optional)" rows={5} className="input resize-none leading-relaxed" />
                <div className="text-right text-xs text-ink-faint mt-1.5">{(currentResponse?.text_response || '').length} characters</div>
              </div>
            )}

            {error && <div className="text-clay text-sm mt-4">{error}</div>}

            <div className="flex items-center justify-between mt-8">
              <button onClick={() => setCurrentIndex(i => Math.max(0, i - 1))} disabled={currentIndex === 0}
                className="text-sm text-ink-faint hover:text-ink-soft disabled:opacity-0 transition-colors">← Back</button>
              <button onClick={handleNext} disabled={!canAdvance || (phase as Phase) === 'submitting'} className="btn-primary px-8">
                {currentIndex === questions.length - 1 ? 'Finish' : 'Continue'}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
