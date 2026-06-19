import { ReactNode } from 'react'

const INPUT =
  'w-full bg-[#161920] border border-white/10 rounded-xl px-4 py-3 text-white text-sm focus:outline-none focus:border-blue-500/50 transition-colors'

export function AuthShell({ children, subtitle }: { children: ReactNode; subtitle: string }) {
  return (
    <div className="min-h-screen bg-[#0A0C10] flex items-center justify-center px-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-10">
          <div className="inline-flex items-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center text-sm font-bold" style={{ fontFamily: 'sans-serif' }}>B</div>
            <div className="text-left">
              <div className="text-lg font-semibold text-white" style={{ fontFamily: 'sans-serif', letterSpacing: '0.05em' }}>BHIS</div>
              <div className="text-[10px] text-white/40 tracking-widest uppercase" style={{ fontFamily: 'sans-serif' }}>Biblical Health Intelligence</div>
            </div>
          </div>
          <p className="text-white/40 text-sm" style={{ fontFamily: 'sans-serif' }}>{subtitle}</p>
        </div>
        <div className="bg-[#0F1117] rounded-2xl border border-white/8 p-8">{children}</div>
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
      <label className="block text-xs text-white/50 uppercase tracking-widest mb-2" style={{ fontFamily: 'sans-serif' }}>{label}</label>
      <input
        type={type}
        value={value}
        onChange={e => onChange(e.target.value)}
        className={INPUT}
        style={{ fontFamily: 'sans-serif' }}
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
    <button
      type="submit"
      disabled={loading}
      className="w-full bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white rounded-xl py-3 text-sm font-medium transition-colors"
      style={{ fontFamily: 'sans-serif' }}
    >
      {loading ? 'Please wait…' : label}
    </button>
  )
}

export function FormError({ message }: { message?: string }) {
  if (!message) return null
  return <div className="text-red-400 text-sm text-center" style={{ fontFamily: 'sans-serif' }} role="alert">{message}</div>
}

export function FormNote({ children }: { children: ReactNode }) {
  return <div className="text-emerald-400 text-sm text-center" style={{ fontFamily: 'sans-serif' }} role="status">{children}</div>
}
