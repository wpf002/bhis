import { useState } from 'react'
import { Link, Navigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import {
  RadarChart, Radar, PolarGrid, PolarAngleAxis, ResponsiveContainer,
  BarChart, Bar, XAxis, YAxis, Tooltip, Cell,
} from 'recharts'
import { churchApi, reportApi } from '../services/api'
import { useAuthStore } from '../hooks/useAuth'
import { PILLAR_LABELS, PILLAR_COLORS, MATURITY_TIER_COLORS } from '../types'
import type { ChurchReport, SuppressedReport, MaturityTier } from '../types'
import { Logo, ScoreRing, Badge, statusFromScore, STATUS_TONE, EmptyState } from '../components/ui'
import clsx from 'clsx'

const TABS = ['Overview', 'The seven areas', 'Your people', 'Where to focus'] as const
type Tab = typeof TABS[number]

const TIER_WORD = (s: number) => s >= 81 ? 'Multiplying' : s >= 61 ? 'Grounded' : s >= 41 ? 'Growing' : s >= 21 ? 'Nominal' : 'Disengaged'

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
    enabled: !!instanceId && (tab === 'Where to focus' || !!selectedPillar),
  })

  if (!churchId) return <Navigate to="/onboarding" replace />

  if (isLoading) {
    return <div className="min-h-screen bg-canvas flex items-center justify-center"><div className="text-ink-faint text-sm">Loading…</div></div>
  }

  if (!dashboard?.health_score) {
    return (
      <div className="min-h-screen bg-canvas">
        <Header name={dashboard?.church?.name} count={0} instanceId={null} onSignOut={clearAuth} />
        <div className="max-w-6xl mx-auto px-6 pt-16">
          <EmptyState
            title="No results yet"
            message="Once enough of your congregation has reflected, your church’s health and insights will gather here."
            action={<Link to="/admin" className="btn-primary">Launch a survey</Link>}
          />
        </div>
      </div>
    )
  }

  const pillarScores = dashboard.pillar_scores || {}
  const pillarList = Object.entries(PILLAR_LABELS).map(([key, label]) => ({
    key, label,
    score: pillarScores[key] || 0,
    color: PILLAR_COLORS[key],
    status: statusFromScore(pillarScores[key] || 0),
  }))
  const radarData = pillarList.slice(0, 6).map(p => ({ subject: p.label.split(' ')[0], score: p.score }))
  const maturityData = Object.entries(dashboard.maturity_distribution || {}).map(([tier, pct]) => ({
    tier, pct: pct as number, color: MATURITY_TIER_COLORS[tier as MaturityTier] || '#9A917F',
  }))
  const healthScore = dashboard.health_score || 0

  return (
    <div className="min-h-screen bg-canvas pb-16">
      <Header name={dashboard.church?.name} count={dashboard.respondent_count || 0} instanceId={instanceId} onSignOut={clearAuth} />

      <div className="max-w-6xl mx-auto px-6 pt-8">
        {/* Hero */}
        <div className="card p-7 mb-6">
          <div className="flex flex-wrap items-center gap-8">
            <ScoreRing score={healthScore} />
            <div className="flex-1 min-w-56">
              <div className="eyebrow mb-1">Overall health</div>
              <h1 className="text-3xl text-ink mb-2">{TIER_WORD(healthScore)}</h1>
              {dashboard.archetype && (
                <span className="inline-flex items-center gap-2 rounded-full bg-gold-soft border border-gold/30 px-3 py-1 text-sm text-[#9A7424]">
                  <span className="w-1.5 h-1.5 rounded-full bg-gold" /> {dashboard.archetype}
                </span>
              )}
            </div>
            <div className="grid grid-cols-3 gap-3 w-full sm:w-auto">
              <Stat label="People" value={String(dashboard.respondent_count || 0)} />
              <Stat label="Areas to watch" value={(dashboard.drift_risk_level || '—').replace(/^\w/, c => c.toUpperCase())} />
              <Stat label="Multiplying" value={`${dashboard.maturity_distribution?.['Multiplying Disciple'] || 0}%`} />
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex flex-wrap gap-1 mb-6 bg-warmth rounded-full p-1 border border-line w-fit">
          {TABS.map(t => (
            <button key={t} role="tab" aria-selected={tab === t} onClick={() => setTab(t)}
              className={clsx('px-4 py-2 rounded-full text-sm transition-all', tab === t ? 'bg-surface text-ink shadow-soft' : 'text-ink-faint hover:text-ink-soft')}>
              {t}
            </button>
          ))}
        </div>

        {tab === 'Overview' && (
          <div className="grid md:grid-cols-3 gap-4">
            <div className="card p-6 md:col-span-2">
              <div className="eyebrow mb-4">The seven areas of health</div>
              <ResponsiveContainer width="100%" height={300}>
                <RadarChart data={radarData}>
                  <PolarGrid stroke="#E9E1D3" />
                  <PolarAngleAxis dataKey="subject" tick={{ fill: '#9A917F', fontSize: 12 }} />
                  <Radar dataKey="score" stroke="#4F7355" fill="#4F7355" fillOpacity={0.18} strokeWidth={2} />
                </RadarChart>
              </ResponsiveContainer>
            </div>
            <div className="card p-6">
              <div className="eyebrow mb-4">Where your people are</div>
              <div className="space-y-3.5">
                {maturityData.map(m => (
                  <div key={m.tier}>
                    <div className="flex justify-between mb-1">
                      <span className="text-xs text-ink-soft">{m.tier}</span>
                      <span className="text-xs font-semibold text-ink">{m.pct}%</span>
                    </div>
                    <div className="h-2 bg-warmth rounded-full overflow-hidden">
                      <div className="h-full rounded-full" style={{ width: `${Math.min(100, m.pct * 2)}%`, background: m.color }} />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {tab === 'The seven areas' && (
          <div className="grid sm:grid-cols-2 gap-3">
            {pillarList.map(p => (
              <button key={p.key} onClick={() => setSelectedPillar(p.key)} aria-label={`View ${p.label}`}
                className="card p-5 text-left hover:shadow-lift transition-shadow">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-ink">{p.label}</span>
                  <span className="text-2xl font-serif text-ink">{Math.round(p.score)}</span>
                </div>
                <div className="h-2 bg-warmth rounded-full overflow-hidden mb-3">
                  <div className="h-full rounded-full" style={{ width: `${p.score}%`, background: p.color }} />
                </div>
                <Badge status={p.status} />
              </button>
            ))}
          </div>
        )}

        {tab === 'Your people' && (
          <div className="grid md:grid-cols-2 gap-4">
            <div className="card p-6">
              <div className="eyebrow mb-4">Spiritual maturity across the congregation</div>
              <ResponsiveContainer width="100%" height={240}>
                <BarChart data={maturityData}>
                  <XAxis dataKey="tier" tick={{ fill: '#9A917F', fontSize: 9 }} axisLine={false} tickLine={false} interval={0} />
                  <YAxis tick={{ fill: '#9A917F', fontSize: 10 }} axisLine={false} tickLine={false} />
                  <Tooltip cursor={{ fill: '#F6F1E7' }} contentStyle={{ background: '#fff', border: '1px solid #E9E1D3', borderRadius: 12, fontSize: 12 }} formatter={(v) => [`${v}%`, '']} />
                  <Bar dataKey="pct" radius={[6, 6, 0, 0]}>
                    {maturityData.map((m, i) => <Cell key={i} fill={m.color} />)}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
            <div className="card p-6">
              <div className="eyebrow mb-4">At a glance</div>
              <div className="space-y-3.5">
                {pillarList.slice(0, 6).map(p => (
                  <div key={p.key} className="flex items-center gap-3">
                    <div className="w-28 text-xs text-ink-soft truncate">{p.label.split(' ')[0]}</div>
                    <div className="flex-1 h-2 bg-warmth rounded-full overflow-hidden">
                      <div className="h-full rounded-full" style={{ width: `${p.score}%`, background: p.color }} />
                    </div>
                    <div className="w-7 text-right text-xs font-semibold text-ink">{Math.round(p.score)}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {tab === 'Where to focus' && <FocusTab report={report} />}
      </div>

      {selectedPillar && (
        <PillarModal pillar={pillarList.find(p => p.key === selectedPillar)!} report={report} onClose={() => setSelectedPillar(null)} />
      )}

      <p className="text-center text-xs text-ink-faint mt-10">
        Every response is anonymous · BHIS helps you shepherd, never surveil
      </p>
    </div>
  )
}

function Header({ name, count, instanceId, onSignOut }: { name?: string; count: number; instanceId: string | null; onSignOut: () => void }) {
  return (
    <header className="border-b border-line bg-surface/80 backdrop-blur sticky top-0 z-10">
      <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
        <Logo />
        <div className="flex items-center gap-4 text-sm">
          <div className="text-right hidden sm:block">
            <div className="text-ink">{name || 'Your Church'}</div>
            <div className="text-xs text-ink-faint">{count} {count === 1 ? 'person' : 'people'} responded</div>
          </div>
          <Link to="/admin" className="text-ink-soft hover:text-ink hidden sm:inline">Manage</Link>
          {instanceId && <a href={reportApi.churchExportUrl(instanceId, 'html')} target="_blank" rel="noreferrer" className="btn-ghost">Export</a>}
          <button onClick={onSignOut} className="text-ink-faint hover:text-ink-soft">Sign out</button>
        </div>
      </div>
    </header>
  )
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-warmth rounded-2xl px-4 py-3 border border-line text-center sm:text-left min-w-24">
      <div className="text-[11px] text-ink-faint mb-0.5">{label}</div>
      <div className="text-lg font-semibold text-ink">{value}</div>
    </div>
  )
}

function FocusTab({ report }: { report?: ChurchReport | SuppressedReport }) {
  if (!report) return <EmptyState title="Gathering insight" message="Recommendations appear once your church has enough responses." />
  if ('suppressed' in report && report.suppressed) return <EmptyState title="Protecting anonymity" message={report.message} />
  const recs = (report as ChurchReport).recommendations || []
  if (recs.length === 0) return <EmptyState title="A healthy sign" message="No priority areas flagged right now — keep doing what you’re doing." />
  return (
    <div className="space-y-4">
      {recs.map(r => (
        <div key={r.priority} className="card p-6">
          <div className="flex items-start justify-between mb-3">
            <div className="font-serif text-lg text-ink">{r.title}</div>
          </div>
          <p className="text-sm text-ink-soft leading-relaxed mb-4">{r.diagnosis}</p>
          <div className="bg-gold-soft rounded-xl p-4 mb-3">
            <div className="eyebrow text-[#9A7424] mb-1.5">A word from Scripture</div>
            <p className="text-sm text-ink italic font-serif">{r.biblical_anchor}</p>
          </div>
          <p className="text-sm text-ink-soft leading-relaxed">{r.intervention}</p>
          <div className="mt-3 text-xs text-ink-faint">Revisit in {r.timeline}</div>
        </div>
      ))}
    </div>
  )
}

const STATUS_MEANING: Record<string, string> = {
  strength: 'A clear strength — this area is healthy across your congregation. Keep nurturing it.',
  moderate: 'Steady. There’s real foundation here, with room to deepen through teaching and practice.',
  gap: 'Growing. This area is still developing and would welcome some intentional attention this season.',
  significant_gap: 'A tender area. One of the most meaningful places to invest care — see the focus suggestions.',
}

type PillarRow = { key: string; label: string; score: number; color: string; status: string }

function PillarModal({ pillar, report, onClose }: { pillar: PillarRow; report?: ChurchReport | SuppressedReport; onClose: () => void }) {
  const recs = report && !('suppressed' in report && report.suppressed)
    ? (report as ChurchReport).recommendations.filter(r => r.pillar === pillar.key) : []
  const tone = STATUS_TONE[pillar.status] || STATUS_TONE.moderate
  return (
    <div className="fixed inset-0 z-50 bg-ink/30 backdrop-blur-sm flex items-center justify-center px-4" role="dialog" aria-modal="true" aria-label={`${pillar.label} detail`} onClick={onClose}>
      <div className="card p-6 max-w-md w-full animate-fade-up" onClick={e => e.stopPropagation()}>
        <div className="flex items-start justify-between mb-4">
          <h3 className="text-xl text-ink">{pillar.label}</h3>
          <button onClick={onClose} aria-label="Close" className="text-ink-faint hover:text-ink text-xl leading-none">×</button>
        </div>
        <div className="flex items-end gap-2 mb-3">
          <span className="text-4xl font-serif" style={{ color: pillar.color }}>{Math.round(pillar.score)}</span>
          <span className="text-ink-faint text-sm mb-1.5">out of 100</span>
          <span className="ml-auto"><Badge status={pillar.status} /></span>
        </div>
        <div className="h-2 bg-warmth rounded-full overflow-hidden mb-4">
          <div className="h-full rounded-full" style={{ width: `${pillar.score}%`, background: pillar.color }} />
        </div>
        <p className="text-sm text-ink-soft leading-relaxed mb-4">{STATUS_MEANING[pillar.status] || ''}</p>
        {recs.length > 0 && (
          <div className="border-t border-line pt-4">
            <div className="eyebrow mb-2">Where to lean in</div>
            {recs.map(r => (
              <div key={r.priority} className="mb-3">
                <div className="font-serif text-ink">{r.title}</div>
                <p className="text-xs text-ink-soft leading-relaxed mt-1">{r.intervention}</p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
