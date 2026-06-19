import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { reportApi } from '../services/api'
import { PILLAR_LABELS } from '../types'
import type { Recommendation } from '../types'
import { Logo, ScoreRing, STATUS_TONE } from '../components/ui'
import clsx from 'clsx'

const TIER_NOTE: Record<string, string> = {
  'Spiritually Disengaged': 'There’s a tender invitation here — small, faithful steps make a real difference.',
  'Nominal': 'A foundation is here. A little more intention could bear real fruit.',
  'Growing': 'You’re growing. Keep leaning into the practices that are stretching you.',
  'Grounded': 'You’re well-rooted. Consider how you might help others grow too.',
  'Multiplying Disciple': 'You’re bearing fruit and helping others do the same. Keep going.',
}

function ExpandableRec({ r }: { r: Recommendation }) {
  const [open, setOpen] = useState(false)
  return (
    <div className="card p-6">
      <button onClick={() => setOpen(o => !o)} className="w-full flex items-start justify-between gap-3 text-left" aria-expanded={open}>
        <div className="font-serif text-lg text-ink">{r.title}</div>
        <span className="text-ink-faint text-sm mt-1">{open ? '–' : '+'}</span>
      </button>
      <p className="text-sm text-ink-soft leading-relaxed mt-2">{r.diagnosis}</p>
      {open && (
        <div className="animate-fade-up mt-4">
          <div className="bg-gold-soft rounded-xl p-4 mb-4">
            <div className="eyebrow text-[#9A7424] mb-1.5">A word from Scripture</div>
            <p className="text-sm text-ink italic font-serif">{r.biblical_anchor}</p>
          </div>
          <p className="text-sm text-ink-soft leading-relaxed">{r.intervention}</p>
          <div className="mt-3 text-xs text-ink-faint">Revisit in {r.timeline}</div>
        </div>
      )}
    </div>
  )
}

export default function IndividualReportPage() {
  const { token } = useParams<{ token: string }>()
  const [emailSent, setEmailSent] = useState(false)

  const { data: report, isLoading, isError } = useQuery({
    queryKey: ['individualReport', token],
    queryFn: () => reportApi.individualByToken(token!),
    enabled: !!token,
    retry: 1,
  })

  const emailReport = async () => {
    if (!token) return
    const email = window.prompt('Email your private reflection link to yourself:')
    if (!email) return
    try { await reportApi.deliver(token, email); setEmailSent(true) } catch { /* noop */ }
  }

  if (isLoading) {
    return <div className="min-h-screen bg-canvas flex items-center justify-center"><div className="text-ink-faint text-sm">Preparing your reflection…</div></div>
  }
  if (isError || !report) {
    return (
      <div className="min-h-screen bg-canvas flex items-center justify-center px-6">
        <div className="text-center text-ink-soft text-sm max-w-sm">
          We couldn’t find this reflection. Your link may have expired, or scoring may still be finishing — try again in a moment.
        </div>
      </div>
    )
  }

  const pillarList = Object.entries(PILLAR_LABELS).map(([key, label]) => {
    const score = Math.round(report.pillar_scores[key] || 0)
    const status = report.pillar_statuses[key] || 'moderate'
    return { key, label, score, tone: STATUS_TONE[status] || STATUS_TONE.moderate }
  })

  return (
    <div className="min-h-screen bg-canvas py-10 px-6">
      <div className="max-w-2xl mx-auto">
        <div className="flex items-center justify-between mb-8">
          <Logo />
          <div className="flex gap-2">
            <a href={reportApi.individualExportUrl(token!, 'html')} target="_blank" rel="noreferrer" className="btn-ghost">Print / Save</a>
            <button onClick={emailReport} className="btn-ghost">{emailSent ? 'Sent ✓' : 'Email me this'}</button>
          </div>
        </div>

        {/* Hero */}
        <div className="card p-8 text-center mb-6 animate-fade-up">
          <div className="eyebrow mb-5">Your personal reflection</div>
          <div className="flex justify-center mb-5"><ScoreRing score={report.composite_score} /></div>
          <h1 className="text-2xl text-ink mb-2">{report.maturity_tier}</h1>
          <p className="text-ink-soft text-sm max-w-md mx-auto leading-relaxed">{TIER_NOTE[report.maturity_tier] || ''}</p>

          {report.credibility_warning && (
            <div className="mt-6 mx-auto max-w-md bg-gold-soft rounded-xl p-4 text-left">
              <div className="text-sm font-semibold text-[#9A7424] mb-1">A gentle observation</div>
              <p className="text-sm text-ink-soft leading-relaxed">
                A few answers point in slightly different directions — which is true of most of us. Take it not as a verdict
                but as an invitation to ask someone you trust: “Does my life look like what I think it does?”
              </p>
            </div>
          )}
        </div>

        {/* Pillars */}
        <div className="card p-6 mb-6">
          <div className="eyebrow mb-5">Across seven areas of life</div>
          <div className="space-y-4">
            {pillarList.map(p => (
              <div key={p.key}>
                <div className="flex justify-between items-center mb-1.5">
                  <span className="text-sm text-ink-soft">{p.label}</span>
                  <div className="flex items-center gap-2.5">
                    <span className={clsx('text-xs font-medium', p.tone.text)}>{p.tone.label}</span>
                    <span className="text-sm font-semibold text-ink w-7 text-right">{p.score}</span>
                  </div>
                </div>
                <div className="h-2 bg-warmth rounded-full overflow-hidden">
                  <div className="h-full rounded-full transition-all" style={{ width: `${p.score}%`, background: p.tone.color }} />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Recommendations */}
        {report.recommendations.length > 0 && (
          <div className="space-y-4 mb-8">
            <div className="eyebrow">Where to lean in next</div>
            {report.recommendations.map(r => <ExpandableRec key={r.priority} r={r} />)}
          </div>
        )}

        <p className="text-center text-xs text-ink-faint">
          Your answers are kept private · This reflection is for your encouragement, not judgment
        </p>
      </div>
    </div>
  )
}
