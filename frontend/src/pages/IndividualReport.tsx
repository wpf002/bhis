import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { reportApi } from '../services/api'
import { PILLAR_LABELS, PILLAR_COLORS } from '../types'
import clsx from 'clsx'

const TIER_COLORS: Record<string, string> = {
  'Spiritually Disengaged': 'text-red-400',
  'Nominal': 'text-orange-400',
  'Growing': 'text-yellow-400',
  'Grounded': 'text-emerald-400',
  'Multiplying Disciple': 'text-blue-400',
}

const STATUS_CONFIG = {
  strength: { text: 'text-emerald-400', label: 'STRENGTH' },
  moderate: { text: 'text-amber-400', label: 'MODERATE' },
  gap: { text: 'text-red-400', label: 'GAP' },
  significant_gap: { text: 'text-red-400', label: 'SIGNIFICANT GAP' },
}

const URGENCY_COLORS: Record<string, string> = {
  HIGH: 'text-red-400 bg-red-500/15 border-red-500/30',
  MEDIUM: 'text-amber-400 bg-amber-500/15 border-amber-500/30',
  LOW: 'text-blue-400 bg-blue-500/15 border-blue-500/30',
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
    const email = window.prompt('Email your private report link to yourself:')
    if (!email) return
    try { await reportApi.deliver(token, email); setEmailSent(true) } catch { /* noop */ }
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-[#0A0C10] flex items-center justify-center">
        <div className="text-white/40 text-sm" style={{ fontFamily: 'sans-serif' }}>Preparing your report…</div>
      </div>
    )
  }

  if (isError || !report) {
    return (
      <div className="min-h-screen bg-[#0A0C10] flex items-center justify-center px-6">
        <div className="text-center text-white/40 text-sm" style={{ fontFamily: 'sans-serif' }}>
          We couldn't find this report. Your report link may have expired, or scoring may still be in progress.
        </div>
      </div>
    )
  }

  const pillarList = Object.entries(PILLAR_LABELS).map(([key, label]) => ({
    key, label,
    score: Math.round(report.pillar_scores[key] || 0),
    color: PILLAR_COLORS[key],
    status: report.pillar_statuses[key] || 'moderate',
  }))

  return (
    <div className="min-h-screen bg-[#0A0C10] text-white py-12 px-6" style={{ fontFamily: 'Georgia, serif' }}>
      <div className="max-w-2xl mx-auto">
        {/* Actions */}
        <div className="flex justify-end gap-3 mb-6" style={{ fontFamily: 'sans-serif' }}>
          <a href={reportApi.individualExportUrl(token!, 'html')} target="_blank" rel="noreferrer"
            className="text-xs text-white/50 hover:text-white/80 border border-white/10 rounded-lg px-3 py-1.5">Print / Save</a>
          <button onClick={emailReport} className="text-xs text-white/50 hover:text-white/80 border border-white/10 rounded-lg px-3 py-1.5">
            {emailSent ? 'Sent ✓' : 'Email me this'}
          </button>
        </div>

        {/* Header */}
        <div className="text-center mb-10">
          <div className="text-[10px] text-white/30 uppercase tracking-widest mb-4" style={{ fontFamily: 'sans-serif' }}>BHIS · Your Personal Assessment</div>
          <div className="text-5xl font-bold mb-2" style={{ fontFamily: 'sans-serif' }}>{report.composite_score}</div>
          <div className={clsx('text-xl mb-1', TIER_COLORS[report.maturity_tier])}>{report.maturity_tier}</div>
          <div className="text-sm text-white/40" style={{ fontFamily: 'sans-serif' }}>Overall Maturity Score</div>

          {report.credibility_warning && (
            <div className="mt-4 mx-auto max-w-sm p-4 rounded-xl bg-amber-500/10 border border-amber-500/20 text-left">
              <div className="text-xs text-amber-400 font-medium mb-1" style={{ fontFamily: 'sans-serif' }}>Consistency Note</div>
              <p className="text-xs text-white/50 leading-relaxed" style={{ fontFamily: 'sans-serif' }}>
                Some responses show a gap between how you see yourself and how your life actually looks. This isn't unusual —
                most of us have blind spots. Use this as an invitation to ask someone you trust: "Does my life look like what I think it does?"
              </p>
            </div>
          )}
        </div>

        {/* Pillar breakdown */}
        <div className="bg-[#0F1117] rounded-2xl border border-white/8 p-6 mb-6">
          <div className="text-[11px] text-white/60 uppercase tracking-widest mb-5" style={{ fontFamily: 'sans-serif' }}>Pillar Breakdown</div>
          <div className="space-y-4">
            {pillarList.map(p => {
              const cfg = STATUS_CONFIG[p.status as keyof typeof STATUS_CONFIG] || STATUS_CONFIG.moderate
              return (
                <div key={p.key}>
                  <div className="flex justify-between items-center mb-1.5">
                    <span className="text-sm text-white/70">{p.label}</span>
                    <div className="flex items-center gap-2">
                      <span className={clsx('text-[10px] font-semibold', cfg.text)} style={{ fontFamily: 'sans-serif' }}>{cfg.label}</span>
                      <span className="text-sm font-bold" style={{ fontFamily: 'sans-serif', color: p.color }}>{p.score}</span>
                    </div>
                  </div>
                  <div className="h-1.5 bg-white/6 rounded-full overflow-hidden">
                    <div className="h-full rounded-full transition-all" style={{ width: `${p.score}%`, background: p.color, opacity: 0.7 }} />
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        {/* Drift */}
        <div className={clsx('rounded-2xl border p-4 mb-6 flex items-center justify-between',
          report.drift_risk_level === 'low' ? 'bg-emerald-500/8 border-emerald-500/20' : 'bg-amber-500/8 border-amber-500/20')}>
          <div>
            <div className="text-[10px] text-white/40 uppercase tracking-widest mb-0.5" style={{ fontFamily: 'sans-serif' }}>Drift Risk</div>
            <div className={clsx('text-lg font-semibold', report.drift_risk_level === 'low' ? 'text-emerald-400' : 'text-amber-400')} style={{ fontFamily: 'sans-serif' }}>
              {report.drift_risk_level.toUpperCase()}
            </div>
          </div>
        </div>

        {/* Recommendations */}
        {report.recommendations.length > 0 && (
          <div className="space-y-4 mb-8">
            <div className="text-[11px] text-white/60 uppercase tracking-widest" style={{ fontFamily: 'sans-serif' }}>Your Growth Areas</div>
            {report.recommendations.map(r => (
              <div key={r.priority} className="bg-[#0F1117] rounded-2xl border border-white/8 p-6">
                <div className="flex items-start justify-between mb-3">
                  <div className="text-white/90 font-medium">{r.title}</div>
                  <span className={clsx('text-[10px] px-2 py-0.5 rounded border font-bold', URGENCY_COLORS[r.urgency])} style={{ fontFamily: 'sans-serif' }}>{r.urgency}</span>
                </div>
                <p className="text-sm text-white/50 leading-relaxed mb-4" style={{ fontFamily: 'sans-serif' }}>{r.diagnosis}</p>
                <div className="bg-blue-500/8 border border-blue-500/15 rounded-xl p-4 mb-4">
                  <div className="text-[10px] text-blue-400 uppercase tracking-widest mb-2" style={{ fontFamily: 'sans-serif' }}>Scripture Anchor</div>
                  <p className="text-xs text-white/60 italic" style={{ fontFamily: 'sans-serif' }}>{r.biblical_anchor}</p>
                </div>
                <p className="text-sm text-white/70 leading-relaxed" style={{ fontFamily: 'sans-serif' }}>{r.intervention}</p>
                <div className="mt-3 text-[10px] text-amber-400 uppercase tracking-widest" style={{ fontFamily: 'sans-serif' }}>Timeline: {r.timeline}</div>
              </div>
            ))}
          </div>
        )}

        <div className="text-center text-xs text-white/20" style={{ fontFamily: 'sans-serif' }}>
          BHIS · Your responses are anonymous · This report is for personal growth, not judgment
        </div>
      </div>
    </div>
  )
}
