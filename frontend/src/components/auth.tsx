import { ReactNode } from 'react'
import { Logo } from './ui'

export function AuthShell({ children, title, subtitle }: { children: ReactNode; title?: string; subtitle: string }) {
  return (
    <div className="min-h-screen bg-canvas flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-md">
        <div className="flex flex-col items-center text-center mb-8">
          <Logo />
          <h1 className="text-2xl text-ink mt-6 mb-1">{title || 'Welcome'}</h1>
          <p className="text-ink-soft text-sm">{subtitle}</p>
        </div>
        <div className="card p-8">{children}</div>
        <p className="text-center text-xs text-ink-faint mt-6">
          Biblical Health Intelligence · A tool for shepherding, not scoring
        </p>
      </div>
    </div>
  )
}

export function Field({
  label, value, onChange, type = 'text', placeholder, required, autoFocus,
}: {
  label: string; value: string; onChange: (v: string) => void
  type?: string; placeholder?: string; required?: boolean; autoFocus?: boolean
}) {
  return (
    <div>
      <label className="label">{label}</label>
      <input
        type={type}
        value={value}
        onChange={e => onChange(e.target.value)}
        className="input"
        placeholder={placeholder}
        required={required}
        autoFocus={autoFocus}
        aria-label={label}
      />
    </div>
  )
}

export function SubmitButton({ loading, label }: { loading: boolean; label: string }) {
  return (
    <button type="submit" disabled={loading} className="btn-primary w-full py-3">
      {loading ? 'Please wait…' : label}
    </button>
  )
}

export function FormError({ message }: { message?: string }) {
  if (!message) return null
  return (
    <div className="rounded-xl bg-clay-soft border border-clay/20 px-4 py-2.5 text-sm text-clay text-center" role="alert">
      {message}
    </div>
  )
}

export function FormNote({ children }: { children: ReactNode }) {
  return (
    <div className="rounded-xl bg-sage-soft border border-sage/20 px-4 py-3 text-sm text-sage-dark text-center" role="status">
      {children}
    </div>
  )
}
