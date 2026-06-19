import { useState } from 'react'
import { Link, Navigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import {
  RadarChart, Radar, PolarGrid, PolarAngleAxis, ResponsiveContainer,
  BarChart, Bar, XAxis, YAxis, Tooltip, Cell,
} from 'recharts'
import { churchApi, reportApi } from '../services/api'
import { useAuthStore } from '../hooks/useAuth'
import { PILLAR_LABELS, PILLAR_COLORS } from '../types'
import type { ChurchReport, SuppressedReport } from '../types'
import clsx from 'clsx'

const TABS = ['Overview', 'Pillars', 'Congregation', 'Actions'] as const
type Tab = typeof TABS[number]

const statusConfig = {
  strength: { bg: 'bg-emerald-500/15', text: 'text-emerald-400', border: 'border-emerald-500/30', label: 'STRENGTH' },
  moderate: { bg: 'bg-amber-500/15', text: 'text-amber-400', border: 'border-amber-500/30', label: 'MODERATE' },
  gap: { bg: 'bg-red-500/15', text: 'text-red-400', border: 'border-red-500/30', label: 'GAP' },
  significant_gap: { bg: 'bg-red-600/20', text: 'text-red-400', border: 'border-red-600/40', label: 'SIGNIFICANT GAP' },
}

const urgencyConfig: Record<string, string> = {
  HIGH: 'bg-red-500/20 text-red-400 border-red-500/40',
  MEDIUM: 'bg-amber-500/20 text-amber-400 border-amber-500/40',
  LOW: 'bg-blue-500/20 text-blue-400 border-blue-500/40',
}

export default function DashboardPage() {
  const [tab, setTab] = useState<Tab>('Overview')
  const [selectedPillar, setSelectedPillar] = useState<string | null>(null)
  const { clearAuth, churchId } = useAuthStore()

  const { data: dashboard, isLoading } = useQuery({
    queryKey: ['dashboard', churchId],
    queryFn: () => churchApi.getDashboard(churchId!),
    enabled: !!churchId,
  })

  const instanceId = dashboard?.survey_instance_id || null

  const { data: report } = useQuery({
    queryKey: ['churchReport', instanceId],
    queryFn: () => reportApi.church(instanceId!),
    enabled: !!instanceId && (tab === 'Actions' || !!selectedPillar),
  })

  if (!churchId) return <Navigate to="/onboarding" replace />

  if (isLoading) {
    return (
      <div className="min-h-screen bg-[#0A0C10] flex items-center justify-center">
        <div className="text-white/40 text-sm" style={{ fontFamily: 'sans-serif' }}>Loading dashboard...</div>
      </div>
    )
  }

  // Empty state — no scored responses yet (or below the anonymity floor).
  if (!dashboard?.health_score) {
    return (
      <div className="min-h-screen bg-[#0A0C10] flex items-center justify-center px-6" style={{ fontFamily: 'sans-serif' }}>
        <div className="text-center max-w-md">
          <div className="text-lg text-white/80 mb-2" style={{ fontFamily: 'Georgia, serif' }}>No results yet</div>
          <p className="text-sm text-white/40 mb-6">
            Once enough of your congregation has completed the assessment, your church's health score and insights appear here.
          </p>
          <div className="flex items-center justify-center gap-3">
            <Link to="/admin" className="bg-blue-600 hover:bg-blue-500 text-white px-5 py-2.5 rounded-xl text-sm font-medium">Launch a survey</Link>
            <button onClick={clearAuth} className="text-xs text-white/30 hover:text-white/60">Sign out</button>
          </div>
        </div>
      </div>
    )
  }

  const pillarScores = dashboard?.pillar_scores || {}
  const pillarList = Object.entries(PILLAR_LABELS).map(([key, label]) => ({
    key,
    label,
    score: pillarScores[key] || 0,
    color: PILLAR_COLORS[key],
    status: pillarScores[key] >= 70 ? 'strength' : pillarScores[key] >= 50 ? 'moderate' : pillarScores[key] >= 35 ? 'gap' : 'significant_gap',
  }))

  const radarData = pillarList.slice(0, 6).map(p => ({
    subject: p.label.split(' ')[0],
    score: p.score,
  }))

  const maturityData = Object.entries(dashboard?.maturity_distribution || {}).map(([tier, pct]) => ({
    tier,
    pct: pct as number,
    color: { 'Spiritually Disengaged': '#FC5C65', Nominal: '#FD9644', Growing: '#F7B731', Grounded: '#26DE81', 'Multiplying Disciple': '#4B7BEC' }[tier] || '#666',
  }))

  const healthScore = dashboard?.health_score || 0

  return (
    <div className="min-h-screen bg-[#0A0C10] text-white" style={{ fontFamily: 'Georgia, serif' }}>
      {/* Top bar */}
      <div className="border-b border-white/8 bg-[#0D0F14]">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center text-xs font-bold" style={{ fontFamily: 'sans-serif' }}>B</div>
            <div>
              <div className="text-sm font-semibold text-white/90" style={{ fontFamily: 'sans-serif', letterSpacing: '0.08em' }}>BHIS</div>
              <div className="text-[10px] text-white/40 tracking-widest uppercase" style={{ fontFamily: 'sans-serif' }}>Biblical Health Intelligence</div>
            </div>
          </div>
          <div className="flex items-center gap-4" style={{ fontFamily: 'sans-serif' }}>
            <div className="text-right">
              <div className="text-sm text-white/80">{dashboard?.church?.name || 'Your Church'}</div>
              <div className="text-xs text-white/40">{dashboard?.respondent_count || 0} Respondents</div>
            </div>
            <Link to="/admin" className="text-xs text-white/40 hover:text-white/70 transition-colors">Manage surveys</Link>
            {instanceId && (
              <a href={reportApi.churchExportUrl(instanceId, 'html')} target="_blank" rel="noreferrer"
                className="text-xs text-white/40 hover:text-white/70 border border-white/10 rounded-lg px-2.5 py-1">Export</a>
            )}
            <button onClick={clearAuth} className="text-xs text-white/30 hover:text-white/60 transition-colors">Sign out</button>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 pt-8">
        {/* Score hero */}
        <div className="bg-[#0F1117] rounded-2xl border border-white/8 p-6 mb-6">
          <div className="flex flex-wrap gap-8 items-center">
            <div className="flex items-center gap-6">
              <div className="relative">
                <svg width="100" height="100" viewBox="0 0 100 100">
                  <circle cx="50" cy="50" r="42" fill="none" stroke="#1a1d26" strokeWidth="10" />
                  <circle cx="50" cy="50" r="42" fill="none" stroke="url(#scoreGrad)" strokeWidth="10"
                    strokeDasharray={`${healthScore / 100 * 263.9} 263.9`}
                    strokeLinecap="round" transform="rotate(-90 50 50)" />
                  <defs>
                    <linearGradient id="scoreGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                      <stop offset="0%" stopColor="#4B7BEC" />
                      <stop offset="100%" stopColor="#26DE81" />
                    </linearGradient>
                  </defs>
                </svg>
                <div className="absolute inset-0 flex flex-col items-center justify-center">
                  <span className="text-2xl font-bold text-white" style={{ fontFamily: 'sans-serif' }}>{Math.round(healthScore)}</span>
                  <span className="text-[9px] text-white/40 tracking-wider uppercase" style={{ fontFamily: 'sans-serif' }}>/100</span>
                </div>
              </div>
              <div>
                <div className="text-2xl text-white/90 mb-1">
                  {healthScore >= 81 ? 'Multiplying' : healthScore >= 61 ? 'Grounded' : healthScore >= 41 ? 'Growing' : healthScore >= 21 ? 'Nominal' : 'Disengaged'}
                </div>
                <div className="text-sm text-white/40 mb-3" style={{ fontFamily: 'sans-serif' }}>Church Health Score</div>
                {dashboard?.archetype && (
                  <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-amber-500/15 border border-amber-500/30">
                    <div className="w-1.5 h-1.5 rounded-full bg-amber-400" />
                    <span className="text-xs text-amber-400 font-medium" style={{ fontFamily: 'sans-serif' }}>{dashboard.archetype}</span>
                  </div>
                )}
              </div>
            </div>

            <div className="flex-1 grid grid-cols-3 gap-3 min-w-64">
              {[
                { label: 'Drift Risk', value: (dashboard?.drift_risk_level || 'N/A').toUpperCase(), color: dashboard?.drift_risk_level === 'low' ? 'text-emerald-400' : 'text-amber-400' },
                { label: 'Respondents', value: String(dashboard?.respondent_count || 0), color: 'text-white/90' },
                { label: 'Multiplying', value: `${dashboard?.maturity_distribution?.['Multiplying Disciple'] || 0}%`, color: 'text-blue-400' },
              ].map(stat => (
                <div key={stat.label} className="bg-[#161920] rounded-xl p-4 border border-white/6">
                  <div className="text-[10px] text-white/40 uppercase tracking-widest mb-1" style={{ fontFamily: 'sans-serif' }}>{stat.label}</div>
                  <div className={clsx('text-xl font-semibold', stat.color)} style={{ fontFamily: 'sans-serif' }}>{stat.value}</div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex gap-1 mb-6 bg-[#0F1117] rounded-xl p-1 border border-white/6 w-fit">
          {TABS.map(t => (
            <button
              key={t}
              role="tab"
              aria-selected={tab === t}
              onClick={() => setTab(t)}
              className={clsx('px-4 py-2 rounded-lg text-sm transition-all', tab === t ? 'bg-white/10 text-white' : 'text-white/40 hover:text-white/70')}
              style={{ fontFamily: 'sans-serif' }}
            >
              {t}
            </button>
          ))}
        </div>

        {/* Overview */}
        {tab === 'Overview' && (
          <div className="grid grid-cols-3 gap-4">
            <div className="col-span-2 bg-[#0F1117] rounded-2xl border border-white/8 p-6">
              <div className="text-[11px] text-white/60 mb-4 uppercase tracking-widest" style={{ fontFamily: 'sans-serif' }}>Pillar Profile</div>
              <ResponsiveContainer width="100%" height={280}>
                <RadarChart data={radarData}>
                  <PolarGrid stroke="#ffffff10" />
                  <PolarAngleAxis dataKey="subject" tick={{ fill: '#ffffff50', fontSize: 11, fontFamily: 'sans-serif' }} />
                  <Radar name="Church" dataKey="score" stroke="#4B7BEC" fill="#4B7BEC" fillOpacity={0.15} strokeWidth={2} />
                </RadarChart>
              </ResponsiveContainer>
            </div>

            <div className="bg-[#0F1117] rounded-2xl border border-white/8 p-6">
              <div className="text-[11px] text-white/60 mb-4 uppercase tracking-widest" style={{ fontFamily: 'sans-serif' }}>Maturity Distribution</div>
              <div className="space-y-3">
                {maturityData.map(m => (
                  <div key={m.tier}>
                    <div className="flex justify-between mb-1">
                      <span className="text-xs text-white/60" style={{ fontFamily: 'sans-serif' }}>{m.tier}</span>
                      <span className="text-xs font-semibold" style={{ fontFamily: 'sans-serif', color: m.color }}>{m.pct}%</span>
                    </div>
                    <div className="h-1.5 bg-white/6 rounded-full overflow-hidden">
                      <div className="h-full rounded-full" style={{ width: `${m.pct * 2}%`, background: m.color, opacity: 0.8 }} />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Pillars */}
        {tab === 'Pillars' && (
          <div className="space-y-3">
            {pillarList.map(p => {
              const cfg = statusConfig[p.status as keyof typeof statusConfig]
              return (
                <button key={p.key} onClick={() => setSelectedPillar(p.key)}
                  aria-label={`View ${p.label} detail`}
                  className="w-full text-left bg-[#0F1117] rounded-2xl border border-white/8 p-5 hover:border-white/20 transition-colors">
                  <div className="flex items-center gap-4">
                    <div className="flex-1">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-white/90">{p.label}</span>
                        <div className="flex items-center gap-3">
                          <span className={clsx('text-[10px] px-2 py-0.5 rounded border font-semibold', cfg.bg, cfg.text, cfg.border)} style={{ fontFamily: 'sans-serif' }}>{cfg.label}</span>
                          <span className="text-xl font-bold" style={{ fontFamily: 'sans-serif', color: p.color }}>{Math.round(p.score)}</span>
                          <span className="text-white/25 text-sm">›</span>
                        </div>
                      </div>
                      <div className="h-2 bg-white/6 rounded-full overflow-hidden">
                        <div className="h-full rounded-full" style={{ width: `${p.score}%`, background: p.color, opacity: 0.8 }} />
                      </div>
                    </div>
                  </div>
                </button>
              )
            })}
          </div>
        )}

        {/* Congregation */}
        {tab === 'Congregation' && (
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-[#0F1117] rounded-2xl border border-white/8 p-6">
              <div className="text-[11px] text-white/60 mb-5 uppercase tracking-widest" style={{ fontFamily: 'sans-serif' }}>Maturity Distribution</div>
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={maturityData}>
                  <XAxis dataKey="tier" tick={{ fill: '#ffffff40', fontSize: 9, fontFamily: 'sans-serif' }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fill: '#ffffff40', fontSize: 10, fontFamily: 'sans-serif' }} axisLine={false} tickLine={false} />
                  <Tooltip contentStyle={{ background: '#1a1d26', border: '1px solid #ffffff15', borderRadius: 8, fontFamily: 'sans-serif', fontSize: 12 }} formatter={(v) => [`${v}%`, '']} />
                  <Bar dataKey="pct" radius={[4, 4, 0, 0]}>
                    {maturityData.map((m, i) => <Cell key={i} fill={m.color} fillOpacity={0.7} />)}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>

            <div className="bg-[#0F1117] rounded-2xl border border-white/8 p-6">
              <div className="text-[11px] text-white/60 mb-4 uppercase tracking-widest" style={{ fontFamily: 'sans-serif' }}>Pillar Breakdown</div>
              <div className="space-y-3">
                {pillarList.slice(0, 6).map(p => (
                  <div key={p.key} className="flex items-center gap-3">
                    <div className="w-28 text-xs text-white/50 truncate" style={{ fontFamily: 'sans-serif' }}>{p.label.split(' ')[0]}</div>
                    <div className="flex-1 h-1.5 bg-white/6 rounded-full overflow-hidden">
                      <div className="h-full rounded-full" style={{ width: `${p.score}%`, background: p.color, opacity: 0.7 }} />
                    </div>
                    <div className="w-8 text-right text-xs text-white/60" style={{ fontFamily: 'sans-serif' }}>{Math.round(p.score)}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Actions — live recommendations from the church report */}
        {tab === 'Actions' && (
          <ActionsTab report={report} />
        )}
      </div>

      {selectedPillar && (
        <PillarModal
          pillar={pillarList.find(p => p.key === selectedPillar)!}
          report={report}
          onClose={() => setSelectedPillar(null)}
        />
      )}

      <div className="max-w-7xl mx-auto px-6 py-6 mt-4">
        <div className="text-center text-xs text-white/20" style={{ fontFamily: 'sans-serif' }}>
          BHIS · All responses anonymous · Data secured and encrypted
        </div>
      </div>
    </div>
  )
}

function ActionsTab({ report }: { report?: ChurchReport | SuppressedReport }) {
  if (!report) {
    return (
      <div className="bg-[#0F1117] rounded-2xl border border-white/8 p-8 text-center">
        <div className="text-white/40 text-sm" style={{ fontFamily: 'sans-serif' }}>Recommendations appear once your church has scored responses.</div>
      </div>
    )
  }
  if ('suppressed' in report && report.suppressed) {
    return (
      <div className="bg-[#0F1117] rounded-2xl border border-white/8 p-8 text-center">
        <div className="text-white/50 text-sm" style={{ fontFamily: 'sans-serif' }}>{report.message}</div>
      </div>
    )
  }
  const recs = report.recommendations || []
  return (
    <div className="space-y-4">
      {recs.length === 0 && (
        <div className="bg-[#0F1117] rounded-2xl border border-white/8 p-8 text-center">
          <div className="text-white/40 text-sm" style={{ fontFamily: 'sans-serif' }}>No priority actions flagged — a healthy sign.</div>
        </div>
      )}
      {recs.map(r => (
        <div key={r.priority} className="bg-[#0F1117] rounded-2xl border border-white/8 p-6" style={{ fontFamily: 'sans-serif' }}>
          <div className="flex items-start justify-between mb-3">
            <div className="text-white/90 font-medium" style={{ fontFamily: 'Georgia, serif' }}>{r.title}</div>
            <span className={clsx('text-[10px] px-2 py-0.5 rounded border font-bold', urgencyConfig[r.urgency])}>{r.urgency}</span>
          </div>
          <p className="text-sm text-white/50 leading-relaxed mb-4">{r.diagnosis}</p>
          <div className="bg-blue-500/8 border border-blue-500/15 rounded-xl p-4 mb-3">
            <div className="text-[10px] text-blue-400 uppercase tracking-widest mb-2">Scripture Anchor</div>
            <p className="text-xs text-white/60 italic">{r.biblical_anchor}</p>
          </div>
          <p className="text-sm text-white/70 leading-relaxed">{r.intervention}</p>
          <div className="mt-3 text-[10px] text-amber-400 uppercase tracking-widest">Timeline: {r.timeline}</div>
        </div>
      ))}
    </div>
  )
}

const STATUS_MEANING: Record<string, string> = {
  strength: 'A clear strength — this dimension is healthy across your congregation. Keep reinforcing it.',
  moderate: 'Moderate. There is real foundation here, with room to deepen through focused teaching and practice.',
  gap: 'A gap. This dimension is lagging and would benefit from intentional attention this season.',
  significant_gap: 'A significant gap. This is one of the most important areas to address — see the recommendations below.',
}

type PillarRow = { key: string; label: string; score: number; color: string; status: string }

function PillarModal({ pillar, report, onClose }: {
  pillar: PillarRow
  report?: ChurchReport | SuppressedReport
  onClose: () => void
}) {
  const recs = report && !('suppressed' in report && report.suppressed)
    ? (report as ChurchReport).recommendations.filter(r => r.pillar === pillar.key)
    : []
  return (
    <div className="fixed inset-0 z-50 bg-black/60 flex items-center justify-center px-4" role="dialog" aria-modal="true"
      aria-label={`${pillar.label} detail`} onClick={onClose}>
      <div className="bg-[#0F1117] border border-white/10 rounded-2xl p-6 max-w-md w-full" style={{ fontFamily: 'sans-serif' }} onClick={e => e.stopPropagation()}>
        <div className="flex items-start justify-between mb-4">
          <div style={{ fontFamily: 'Georgia, serif' }} className="text-white/90 text-lg">{pillar.label}</div>
          <button onClick={onClose} aria-label="Close" className="text-white/40 hover:text-white/80 text-lg leading-none">×</button>
        </div>
        <div className="flex items-end gap-2 mb-4">
          <span className="text-4xl font-bold" style={{ color: pillar.color }}>{Math.round(pillar.score)}</span>
          <span className="text-white/30 text-sm mb-1">/100</span>
        </div>
        <div className="h-2 bg-white/6 rounded-full overflow-hidden mb-4">
          <div className="h-full rounded-full" style={{ width: `${pillar.score}%`, background: pillar.color, opacity: 0.8 }} />
        </div>
        <p className="text-sm text-white/60 leading-relaxed mb-4">{STATUS_MEANING[pillar.status] || ''}</p>
        {recs.length > 0 && (
          <div className="border-t border-white/8 pt-4">
            <div className="text-[10px] text-white/40 uppercase tracking-widest mb-2">Recommended focus</div>
            {recs.map(r => (
              <div key={r.priority} className="mb-3">
                <div className="text-sm text-white/80" style={{ fontFamily: 'Georgia, serif' }}>{r.title}</div>
                <p className="text-xs text-white/50 leading-relaxed mt-1">{r.intervention}</p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
