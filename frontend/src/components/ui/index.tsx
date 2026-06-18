import clsx from 'clsx'
import { ReactNode } from 'react'

// ── Badge ─────────────────────────────────────────────────────────────────────

interface BadgeProps {
  label: string
  variant?: 'blue' | 'green' | 'amber' | 'red' | 'neutral'
  size?: 'sm' | 'xs'
}

const BADGE_VARIANTS = {
  blue:    'bg-blue-500/15 text-blue-400 border-blue-500/30',
  green:   'bg-emerald-500/15 text-emerald-400 border-emerald-500/30',
  amber:   'bg-amber-500/15 text-amber-400 border-amber-500/30',
  red:     'bg-red-500/15 text-red-400 border-red-500/30',
  neutral: 'bg-white/8 text-white/50 border-white/10',
}

export function Badge({ label, variant = 'neutral', size = 'xs' }: BadgeProps) {
  return (
    <span
      className={clsx(
        'inline-flex items-center rounded-lg border font-semibold uppercase tracking-wider',
        BADGE_VARIANTS[variant],
        size === 'xs' ? 'text-[10px] px-2 py-0.5' : 'text-xs px-2.5 py-1'
      )}
      style={{ fontFamily: 'sans-serif' }}
    >
      {label}
    </span>
  )
}

// ── Card ──────────────────────────────────────────────────────────────────────

export function Card({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <div className={clsx('bg-[#0F1117] rounded-2xl border border-white/8 p-6', className)}>
      {children}
    </div>
  )
}

// ── SectionLabel ──────────────────────────────────────────────────────────────

export function SectionLabel({ children }: { children: ReactNode }) {
  return (
    <div className="text-[11px] text-white/60 uppercase tracking-widest mb-4" style={{ fontFamily: 'sans-serif' }}>
      {children}
    </div>
  )
}

// ── ScoreRing ─────────────────────────────────────────────────────────────────

interface ScoreRingProps {
  score: number
  size?: number
  strokeWidth?: number
}

export function ScoreRing({ score, size = 100, strokeWidth = 10 }: ScoreRingProps) {
  const r = (size / 2) - strokeWidth
  const circumference = 2 * Math.PI * r
  const filled = (score / 100) * circumference
  const cx = size / 2
  const cy = size / 2

  return (
    <div className="relative" style={{ width: size, height: size }}>
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
        <circle cx={cx} cy={cy} r={r} fill="none" stroke="#1a1d26" strokeWidth={strokeWidth} />
        <circle
          cx={cx} cy={cy} r={r}
          fill="none"
          stroke="url(#scoreGrad)"
          strokeWidth={strokeWidth}
          strokeDasharray={`${filled} ${circumference}`}
          strokeLinecap="round"
          transform={`rotate(-90 ${cx} ${cy})`}
        />
        <defs>
          <linearGradient id="scoreGrad" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#4B7BEC" />
            <stop offset="100%" stopColor="#26DE81" />
          </linearGradient>
        </defs>
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-2xl font-bold text-white" style={{ fontFamily: 'sans-serif' }}>{Math.round(score)}</span>
        <span className="text-[9px] text-white/40 tracking-wider uppercase" style={{ fontFamily: 'sans-serif' }}>/100</span>
      </div>
    </div>
  )
}

// ── PillarBar ─────────────────────────────────────────────────────────────────

interface PillarBarProps {
  label: string
  score: number
  color: string
  benchmark?: number
}

export function PillarBar({ label, score, color, benchmark }: PillarBarProps) {
  return (
    <div>
      <div className="flex justify-between items-center mb-1.5">
        <span className="text-sm text-white/70">{label}</span>
        <span className="text-sm font-bold" style={{ fontFamily: 'sans-serif', color }}>{Math.round(score)}</span>
      </div>
      <div className="relative h-1.5 bg-white/6 rounded-full overflow-hidden">
        <div className="h-full rounded-full transition-all" style={{ width: `${score}%`, background: color, opacity: 0.75 }} />
        {benchmark !== undefined && (
          <div className="absolute top-0 h-full w-0.5 bg-white/25" style={{ left: `${benchmark}%` }} />
        )}
      </div>
    </div>
  )
}

// ── TopBar ────────────────────────────────────────────────────────────────────

interface TopBarProps {
  churchName?: string
  subtitle?: string
  onSignOut?: () => void
}

export function TopBar({ churchName, subtitle, onSignOut }: TopBarProps) {
  return (
    <div className="border-b border-white/8 bg-[#0D0F14]">
      <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center text-xs font-bold" style={{ fontFamily: 'sans-serif' }}>B</div>
          <div>
            <div className="text-sm font-semibold text-white/90" style={{ fontFamily: 'sans-serif', letterSpacing: '0.08em' }}>BHIS</div>
            <div className="text-[10px] text-white/40 tracking-widest uppercase" style={{ fontFamily: 'sans-serif' }}>Biblical Health Intelligence</div>
          </div>
        </div>
        {(churchName || onSignOut) && (
          <div className="flex items-center gap-4">
            {churchName && (
              <div className="text-right">
                <div className="text-sm text-white/80" style={{ fontFamily: 'sans-serif' }}>{churchName}</div>
                {subtitle && <div className="text-xs text-white/40" style={{ fontFamily: 'sans-serif' }}>{subtitle}</div>}
              </div>
            )}
            {onSignOut && (
              <button onClick={onSignOut} className="text-xs text-white/30 hover:text-white/60 transition-colors" style={{ fontFamily: 'sans-serif' }}>
                Sign out
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

// ── EmptyState ────────────────────────────────────────────────────────────────

export function EmptyState({ message, sub }: { message: string; sub?: string }) {
  return (
    <div className="bg-[#0F1117] rounded-2xl border border-white/8 p-12 text-center">
      <div className="text-white/40 mb-2">{message}</div>
      {sub && <div className="text-white/20 text-sm" style={{ fontFamily: 'sans-serif' }}>{sub}</div>}
    </div>
  )
}
