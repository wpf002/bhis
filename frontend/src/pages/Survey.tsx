import { useState, useEffect, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { surveyApi, responseApi } from '../services/api'
import type { Question, ResponseEntry } from '../types'
import { loadSurvey, saveSurvey, saveAnswers, clearSurvey, rememberReportToken } from '../lib/surveySession'
import clsx from 'clsx'

type Phase = 'intro' | 'questions' | 'submitting' | 'done'

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

  // Resume an in-progress survey on this device.
  useEffect(() => {
    if (!instanceId) return
    const saved = loadSurvey(instanceId)
    if (saved) {
      setSession({ id: saved.sessionId, token: saved.token })
      setResponses(saved.answers || {})
      setPhase('questions')
    }
  }, [instanceId])

  // Warn before leaving mid-survey.
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
      setError('This survey is not available right now.')
    }
  }

  const currentQ: Question | undefined = questions[currentIndex]
  const progress = questions.length > 0 ? (currentIndex / questions.length) * 100 : 0
  const currentResponse = currentQ ? responses[currentQ.id] : undefined

  const record = (entry: Partial<ResponseEntry>) => {
    if (!currentQ || !instanceId) return
    const next = {
      ...responses,
      [currentQ.id]: {
        question_id: currentQ.id,
        response_time_seconds: Math.round((Date.now() - startTime.current) / 1000),
        ...entry,
      },
    }
    setResponses(next)
    saveAnswers(instanceId, next) // autosave
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
      setError(e?.response?.data?.detail || 'Could not submit. Please try again.')
      setPhase('questions')
    }
  }

  // ── Intro / consent ─────────────────────────────────────────────────────────
  if (phase === 'intro') {
    return (
      <div className="min-h-screen bg-[#0A0C10] flex items-center justify-center px-6">
        <div className="w-full max-w-lg text-center">
          <div className="text-[10px] text-white/30 uppercase tracking-widest mb-4" style={{ fontFamily: 'sans-serif' }}>BHIS Assessment</div>
          <h1 className="text-2xl text-white/90 mb-4">A few honest minutes</h1>
          <p className="text-white/50 text-sm leading-relaxed mb-6" style={{ fontFamily: 'sans-serif' }}>
            This assessment helps your church understand its spiritual health. There are no right or wrong answers —
            answer honestly. It takes about {meta?.estimated_minutes ?? 10}–{(meta?.estimated_minutes ?? 10) + 2} minutes
            {meta ? ` and has ${meta.question_count} questions` : ''}.
          </p>
          <div className="bg-[#0F1117] border border-white/8 rounded-xl p-4 mb-6 text-left">
            <div className="text-xs text-emerald-400 font-medium mb-1" style={{ fontFamily: 'sans-serif' }}>Your responses are anonymous</div>
            <p className="text-xs text-white/40 leading-relaxed" style={{ fontFamily: 'sans-serif' }}>
              Your church sees only combined results, never your individual answers — and cannot link any response back to you.
              You'll get your own private report at the end.
            </p>
          </div>
          {error && <div className="text-red-400 text-sm mb-4" style={{ fontFamily: 'sans-serif' }}>{error}</div>}
          <button onClick={begin} className="bg-blue-600 hover:bg-blue-500 text-white px-8 py-3 rounded-xl text-sm font-medium transition-colors" style={{ fontFamily: 'sans-serif' }}>
            Start assessment →
          </button>
        </div>
      </div>
    )
  }

  if (phase === 'done') {
    return (
      <div className="min-h-screen bg-[#0A0C10] flex items-center justify-center px-6">
        <div className="text-center">
          <div className="text-emerald-400 text-3xl mb-3">✓</div>
          <div className="text-white/80 text-lg mb-1">Thank you</div>
          <div className="text-white/40 text-sm" style={{ fontFamily: 'sans-serif' }}>Preparing your private report…</div>
        </div>
      </div>
    )
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-[#0A0C10] flex items-center justify-center">
        <div className="text-white/40 text-sm" style={{ fontFamily: 'sans-serif' }}>Loading assessment…</div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-[#0A0C10] flex flex-col">
      <div className="border-b border-white/8 bg-[#0D0F14] px-6 py-4">
        <div className="max-w-2xl mx-auto flex items-center justify-between">
          <div className="text-sm font-semibold text-white/60" style={{ fontFamily: 'sans-serif', letterSpacing: '0.08em' }}>BHIS</div>
          <div className="text-xs text-white/40" style={{ fontFamily: 'sans-serif' }}>{currentIndex + 1} of {questions.length}</div>
        </div>
        <div className="max-w-2xl mx-auto mt-3">
          <div className="h-0.5 bg-white/6 rounded-full overflow-hidden" role="progressbar" aria-valuenow={Math.round(progress)} aria-valuemin={0} aria-valuemax={100}>
            <div className="h-full bg-blue-500 rounded-full transition-all duration-500" style={{ width: `${progress}%` }} />
          </div>
        </div>
      </div>

      <div className="flex-1 flex items-center justify-center px-6 py-10">
        {currentQ && (
          <div key={currentIndex} className="w-full max-w-2xl animate-fade-up">
            <div className="mb-6">
              <span className="text-[10px] text-white/30 uppercase tracking-widest" style={{ fontFamily: 'sans-serif' }}>{currentQ.pillar.replace(/_/g, ' ')}</span>
            </div>
            <h2 className="text-xl text-white/90 leading-relaxed mb-8">{currentQ.question_text}</h2>

            {currentQ.question_type === 'likert' && (
              <div className="space-y-2">
                {[[1, 'Strongly Disagree'], [2, 'Disagree'], [3, 'Neutral'], [4, 'Agree'], [5, 'Strongly Agree']].map(([val, label]) => (
                  <button key={val} onClick={() => record({ likert_value: Number(val) })}
                    className={clsx('w-full flex items-center gap-4 px-5 py-4 rounded-xl border text-left transition-all',
                      currentResponse?.likert_value === val ? 'bg-blue-600/20 border-blue-500/50 text-white' : 'bg-[#0F1117] border-white/8 text-white/60 hover:border-white/20 hover:text-white/80')}>
                    <div className={clsx('w-5 h-5 rounded-full border-2 flex items-center justify-center flex-shrink-0', currentResponse?.likert_value === val ? 'border-blue-400 bg-blue-400' : 'border-white/20')}>
                      {currentResponse?.likert_value === val && <div className="w-2 h-2 rounded-full bg-white" />}
                    </div>
                    <span style={{ fontFamily: 'sans-serif' }}>{label as string}</span>
                  </button>
                ))}
              </div>
            )}

            {['mc', 'scenario', 'behavioral_frequency'].includes(currentQ.question_type) && (
              <div className="space-y-2">
                {currentQ.options.map(opt => (
                  <button key={opt.id} onClick={() => record({ selected_option_id: opt.id })}
                    className={clsx('w-full flex items-start gap-4 px-5 py-4 rounded-xl border text-left transition-all',
                      currentResponse?.selected_option_id === opt.id ? 'bg-blue-600/20 border-blue-500/50 text-white' : 'bg-[#0F1117] border-white/8 text-white/60 hover:border-white/20 hover:text-white/80')}>
                    <span className={clsx('text-xs font-bold mt-0.5 flex-shrink-0 w-5', currentResponse?.selected_option_id === opt.id ? 'text-blue-400' : 'text-white/30')} style={{ fontFamily: 'sans-serif' }}>{opt.option_letter.toUpperCase()}</span>
                    <span className="leading-relaxed" style={{ fontFamily: 'sans-serif' }}>{opt.option_text}</span>
                  </button>
                ))}
              </div>
            )}

            {currentQ.question_type === 'forced_prioritization' && (
              <div className="space-y-2">
                <p className="text-xs text-white/40 mb-3" style={{ fontFamily: 'sans-serif' }}>Tap in order, from most to least important.</p>
                {currentQ.options.map(opt => {
                  const rank = (currentResponse?.ranking_order || []).indexOf(opt.option_letter)
                  return (
                    <button key={opt.id} onClick={() => toggleRank(opt.option_letter)}
                      className={clsx('w-full flex items-center gap-4 px-5 py-4 rounded-xl border text-left transition-all',
                        rank >= 0 ? 'bg-blue-600/20 border-blue-500/50 text-white' : 'bg-[#0F1117] border-white/8 text-white/60 hover:border-white/20 hover:text-white/80')}>
                      <span className={clsx('w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0',
                        rank >= 0 ? 'bg-blue-500 text-white' : 'border border-white/20 text-white/30')} style={{ fontFamily: 'sans-serif' }}>
                        {rank >= 0 ? rank + 1 : ''}
                      </span>
                      <span className="leading-relaxed" style={{ fontFamily: 'sans-serif' }}>{opt.option_text}</span>
                    </button>
                  )
                })}
              </div>
            )}

            {currentQ.question_type === 'open_ended' && (
              <div>
                <textarea value={currentResponse?.text_response || ''} onChange={e => record({ text_response: e.target.value })}
                  placeholder="Write your honest answer here… (optional)" rows={5}
                  className="w-full bg-[#0F1117] border border-white/10 rounded-xl px-5 py-4 text-white/80 text-sm focus:outline-none focus:border-blue-500/40 resize-none leading-relaxed"
                  style={{ fontFamily: 'sans-serif' }} />
                <div className="text-right text-[11px] text-white/30 mt-1.5" style={{ fontFamily: 'sans-serif' }}>
                  {(currentResponse?.text_response || '').length} characters
                </div>
              </div>
            )}

            {error && <div className="text-red-400 text-sm mt-4" style={{ fontFamily: 'sans-serif' }}>{error}</div>}

            <div className="flex items-center justify-between mt-8">
              <button onClick={() => setCurrentIndex(i => Math.max(0, i - 1))} disabled={currentIndex === 0}
                className="text-sm text-white/30 hover:text-white/60 disabled:opacity-0 transition-colors" style={{ fontFamily: 'sans-serif' }}>← Back</button>
              <button onClick={handleNext} disabled={!canAdvance || (phase as Phase) === 'submitting'}
                className="bg-blue-600 hover:bg-blue-500 disabled:opacity-30 text-white px-8 py-3 rounded-xl text-sm font-medium transition-colors" style={{ fontFamily: 'sans-serif' }}>
                {currentIndex === questions.length - 1 ? 'Submit' : 'Next →'}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
