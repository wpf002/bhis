import clsx from 'clsx'
import { ReactNode } from 'react'

// ── Brand mark ────────────────────────────────────────────────────────────────

export function Logo({ withWordmark = true }: { withWordmark?: boolean }) {
  return (
    <div className="inline-flex items-center gap-3">
      <div className="w-11 h-11 rounded-2xl bg-sage flex items-center justify-center shadow-soft">
        {/* simple sprout — growth & life */}
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <path d="M12 21V11" stroke="#F6F1E7" strokeWidth="1.8" strokeLinecap="round" />
          <path d="M12 12C12 8.5 9 6.5 5.5 6.5C5.5 10 8 12 12 12Z" fill="#F6F1E7" />
          <path d="M12 10.5C12 7.5 14.5 5 18 5C18 8.2 15.5 10.5 12 10.5Z" fill="#CFE0CC" />
        </svg>
      </div>
      {withWordmark && (
        <div className="text-left leading-tight">
          <div className="font-serif text-lg text-ink">BHIS</div>
          <div className="text-[10px] tracking-[0.14em] uppercase text-ink-faint">Church Health</div>
        </div>
      )}
    </div>
  )
}

// ── Card ──────────────────────────────────────────────────────────────────────

export function Card({ children, className }: { children: ReactNode; className?: string }) {
  return <div className={clsx('card p-6', className)}>{children}</div>
}

// ── Status tones (warm, encouraging — not red/green alerts) ───────────────────

export const STATUS_TONE: Record<string, { label: string; color: string; text: string; bg: string; border: string }> = {
  strength:        { label: 'Strength',    color: '#4F7355', text: 'text-sage-dark', bg: 'bg-sage-soft',  border: 'border-sage/25' },
  moderate:        { label: 'Steady',      color: '#C39A4A', text: 'text-[#9A7424]', bg: 'bg-gold-soft',  border: 'border-gold/30' },
  gap:             { label: 'Growing',     color: '#BE6E47', text: 'text-clay',      bg: 'bg-clay-soft',  border: 'border-clay/25' },
  significant_gap: { label: 'Tender area', color: '#A85638', text: 'text-clay',      bg: 'bg-clay-soft',  border: 'border-clay/30' },
}

export function statusFromScore(score: number): keyof typeof STATUS_TONE {
  if (score >= 70) return 'strength'
  if (score >= 50) return 'moderate'
  if (score >= 35) return 'gap'
  return 'significant_gap'
}

export function Badge({ status }: { status: string }) {
  const t = STATUS_TONE[status] || STATUS_TONE.moderate
  return (
    <span className={clsx('inline-flex items-center rounded-full border px-2.5 py-0.5 text-[11px] font-medium', t.bg, t.text, t.border)}>
      {t.label}
    </span>
  )
}

// ── Score ring ────────────────────────────────────────────────────────────────

export function ScoreRing({ score, size = 132, strokeWidth = 12 }: { score: number; size?: number; strokeWidth?: number }) {
  const r = size / 2 - strokeWidth
  const circ = 2 * Math.PI * r
  const filled = (Math.max(0, Math.min(100, score)) / 100) * circ
  const c = size / 2
  return (
    <div className="relative" style={{ width: size, height: size }}>
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
        <circle cx={c} cy={c} r={r} fill="none" stroke="#ECE4D6" strokeWidth={strokeWidth} />
        <circle
          cx={c} cy={c} r={r} fill="none" stroke="url(#ringGrad)" strokeWidth={strokeWidth}
          strokeDasharray={`${filled} ${circ}`} strokeLinecap="round" transform={`rotate(-90 ${c} ${c})`}
          style={{ transition: 'stroke-dasharray 0.8s ease-out' }}
        />
        <defs>
          <linearGradient id="ringGrad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#4F7355" />
            <stop offset="100%" stopColor="#C39A4A" />
          </linearGradient>
        </defs>
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="font-serif text-4xl text-ink leading-none">{Math.round(score)}</span>
        <span className="text-[10px] tracking-wider uppercase text-ink-faint mt-1">out of 100</span>
      </div>
    </div>
  )
}

// ── Pillar bar ────────────────────────────────────────────────────────────────

export function PillarBar({ label, score, color }: { label: string; score: number; color: string }) {
  return (
    <div>
      <div className="flex justify-between items-center mb-1.5">
        <span className="text-sm text-ink-soft">{label}</span>
        <span className="text-sm font-semibold text-ink">{Math.round(score)}</span>
      </div>
      <div className="h-2 bg-warmth rounded-full overflow-hidden">
        <div className="h-full rounded-full transition-all" style={{ width: `${score}%`, background: color }} />
      </div>
    </div>
  )
}

// ── Empty state ───────────────────────────────────────────────────────────────

export function EmptyState({ title, message, action }: { title: string; message: string; action?: ReactNode }) {
  return (
    <div className="card p-12 text-center">
      <h3 className="text-xl text-ink mb-2">{title}</h3>
      <p className="text-ink-soft text-sm max-w-md mx-auto mb-6">{message}</p>
      {action}
    </div>
  )
}
