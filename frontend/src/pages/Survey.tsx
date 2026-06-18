import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { surveyApi, responseApi, scoringApi } from '../services/api'
import type { Question, ResponseEntry } from '../types'
import clsx from 'clsx'

export default function SurveyPage() {
  const { instanceId } = useParams<{ instanceId: string }>()
  const navigate = useNavigate()

  const [sessionId, setSessionId] = useState<string | null>(null)
  const [currentIndex, setCurrentIndex] = useState(0)
  const [responses, setResponses] = useState<Record<string, ResponseEntry>>({})
  const [submitting, setSubmitting] = useState(false)
  const [startTime, setStartTime] = useState<number>(Date.now())

  const { data: questions = [], isLoading } = useQuery({
    queryKey: ['questions', instanceId],
    queryFn: () => surveyApi.getQuestions(instanceId!),
    enabled: !!instanceId,
  })

  useEffect(() => {
    if (instanceId && !sessionId) {
      responseApi.startSession(instanceId).then(session => {
        setSessionId(session.id)
      })
    }
  }, [instanceId])

  const currentQ: Question | undefined = questions[currentIndex]
  const progress = questions.length > 0 ? (currentIndex / questions.length) * 100 : 0
  const currentResponse = currentQ ? responses[currentQ.id] : undefined

  const handleOptionSelect = (optionId: string) => {
    if (!currentQ) return
    setResponses(prev => ({
      ...prev,
      [currentQ.id]: {
        question_id: currentQ.id,
        selected_option_id: optionId,
        response_time_seconds: Math.round((Date.now() - startTime) / 1000),
      },
    }))
    setStartTime(Date.now())
  }

  const handleLikert = (value: number) => {
    if (!currentQ) return
    setResponses(prev => ({
      ...prev,
      [currentQ.id]: {
        question_id: currentQ.id,
        likert_value: value,
        response_time_seconds: Math.round((Date.now() - startTime) / 1000),
      },
    }))
    setStartTime(Date.now())
  }

  const handleTextResponse = (text: string) => {
    if (!currentQ) return
    setResponses(prev => ({
      ...prev,
      [currentQ.id]: { question_id: currentQ.id, text_response: text },
    }))
  }

  const canAdvance = currentQ && (
    currentQ.question_type === 'open_ended' ||
    responses[currentQ.id] !== undefined
  )

  const handleNext = () => {
    if (currentIndex < questions.length - 1) {
      setCurrentIndex(i => i + 1)
    } else {
      handleSubmit()
    }
  }

  const handleSubmit = async () => {
    if (!sessionId) return
    setSubmitting(true)
    try {
      const responseList = Object.values(responses)
      await responseApi.submitResponses(sessionId, responseList)
      await responseApi.completeSession(sessionId)
      await scoringApi.scoreIndividual(sessionId)
      navigate(`/report/${sessionId}`)
    } catch (e) {
      console.error(e)
    } finally {
      setSubmitting(false)
    }
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-[#0A0C10] flex items-center justify-center">
        <div className="text-white/40 text-sm" style={{ fontFamily: 'sans-serif' }}>Loading assessment...</div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-[#0A0C10] flex flex-col">
      {/* Header */}
      <div className="border-b border-white/8 bg-[#0D0F14] px-6 py-4">
        <div className="max-w-2xl mx-auto flex items-center justify-between">
          <div className="text-sm font-semibold text-white/60" style={{ fontFamily: 'sans-serif', letterSpacing: '0.08em' }}>BHIS</div>
          <div className="text-xs text-white/40" style={{ fontFamily: 'sans-serif' }}>
            {currentIndex + 1} of {questions.length}
          </div>
        </div>
        {/* Progress bar */}
        <div className="max-w-2xl mx-auto mt-3">
          <div className="h-0.5 bg-white/6 rounded-full overflow-hidden">
            <div className="h-full bg-blue-500 rounded-full transition-all duration-500" style={{ width: `${progress}%` }} />
          </div>
        </div>
      </div>

      {/* Question */}
      <div className="flex-1 flex items-center justify-center px-6 py-10">
        {currentQ && (
          <div className="w-full max-w-2xl">
            {/* Pillar badge */}
            <div className="mb-6">
              <span className="text-[10px] text-white/30 uppercase tracking-widest" style={{ fontFamily: 'sans-serif' }}>
                {currentQ.pillar.replace(/_/g, ' ')}
              </span>
            </div>

            {/* Question text */}
            <h2 className="text-xl text-white/90 leading-relaxed mb-8">
              {currentQ.question_text}
            </h2>

            {/* Likert */}
            {currentQ.question_type === 'likert' && (
              <div className="space-y-2">
                {[
                  [1, 'Strongly Disagree'],
                  [2, 'Disagree'],
                  [3, 'Neutral'],
                  [4, 'Agree'],
                  [5, 'Strongly Agree'],
                ].map(([val, label]) => (
                  <button
                    key={val}
                    onClick={() => handleLikert(Number(val))}
                    className={clsx(
                      'w-full flex items-center gap-4 px-5 py-4 rounded-xl border text-left transition-all',
                      currentResponse?.likert_value === val
                        ? 'bg-blue-600/20 border-blue-500/50 text-white'
                        : 'bg-[#0F1117] border-white/8 text-white/60 hover:border-white/20 hover:text-white/80'
                    )}
                  >
                    <div className={clsx(
                      'w-5 h-5 rounded-full border-2 flex items-center justify-center flex-shrink-0',
                      currentResponse?.likert_value === val ? 'border-blue-400 bg-blue-400' : 'border-white/20'
                    )}>
                      {currentResponse?.likert_value === val && (
                        <div className="w-2 h-2 rounded-full bg-white" />
                      )}
                    </div>
                    <span style={{ fontFamily: 'sans-serif' }}>{label as string}</span>
                  </button>
                ))}
              </div>
            )}

            {/* MC / Scenario / Behavioral Frequency */}
            {['mc', 'scenario', 'behavioral_frequency'].includes(currentQ.question_type) && (
              <div className="space-y-2">
                {currentQ.options.map(opt => (
                  <button
                    key={opt.id}
                    onClick={() => handleOptionSelect(opt.id)}
                    className={clsx(
                      'w-full flex items-start gap-4 px-5 py-4 rounded-xl border text-left transition-all',
                      currentResponse?.selected_option_id === opt.id
                        ? 'bg-blue-600/20 border-blue-500/50 text-white'
                        : 'bg-[#0F1117] border-white/8 text-white/60 hover:border-white/20 hover:text-white/80'
                    )}
                  >
                    <span className={clsx(
                      'text-xs font-bold mt-0.5 flex-shrink-0 w-5',
                      currentResponse?.selected_option_id === opt.id ? 'text-blue-400' : 'text-white/30'
                    )} style={{ fontFamily: 'sans-serif' }}>
                      {opt.option_letter.toUpperCase()}
                    </span>
                    <span className="leading-relaxed" style={{ fontFamily: 'sans-serif' }}>{opt.option_text}</span>
                  </button>
                ))}
              </div>
            )}

            {/* Open ended */}
            {currentQ.question_type === 'open_ended' && (
              <textarea
                value={currentResponse?.text_response || ''}
                onChange={e => handleTextResponse(e.target.value)}
                placeholder="Write your honest answer here..."
                rows={5}
                className="w-full bg-[#0F1117] border border-white/10 rounded-xl px-5 py-4 text-white/80 text-sm focus:outline-none focus:border-blue-500/40 resize-none leading-relaxed"
                style={{ fontFamily: 'sans-serif' }}
              />
            )}

            {/* Navigation */}
            <div className="flex items-center justify-between mt-8">
              <button
                onClick={() => setCurrentIndex(i => Math.max(0, i - 1))}
                disabled={currentIndex === 0}
                className="text-sm text-white/30 hover:text-white/60 disabled:opacity-0 transition-colors"
                style={{ fontFamily: 'sans-serif' }}
              >
                ← Back
              </button>
              <button
                onClick={handleNext}
                disabled={!canAdvance || submitting}
                className="bg-blue-600 hover:bg-blue-500 disabled:opacity-30 text-white px-8 py-3 rounded-xl text-sm font-medium transition-colors"
                style={{ fontFamily: 'sans-serif' }}
              >
                {submitting ? 'Submitting...' : currentIndex === questions.length - 1 ? 'Submit' : 'Next →'}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
