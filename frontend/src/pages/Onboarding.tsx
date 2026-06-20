import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import { churchApi } from '../services/api'
import { useAuthStore } from '../hooks/useAuth'
import { Logo } from '../components/ui'
import clsx from 'clsx'

const SIZE_OPTIONS = ['Under 100', '100–250', '250–500', '500–1000', '1000+']
const PROFILE_OPTIONS = ['Evangelical', 'Reformed', 'Baptist', 'Non-denominational', 'Charismatic', 'Anglican', 'Methodist', 'Lutheran', 'Other']

export default function OnboardingPage() {
  const navigate = useNavigate()
  const { setChurchId } = useAuthStore()
  const [step, setStep] = useState(1)
  const [form, setForm] = useState({ name: '', denomination: '', size_range: '', city: '', state: '', theological_profile: '' })
  const update = (k: string, v: string) => setForm(f => ({ ...f, [k]: v }))

  const mutation = useMutation({
    mutationFn: () => churchApi.create(form),
    onSuccess: (data) => { setChurchId(data.id); navigate('/admin') },
  })

  const choice = (selected: boolean) => clsx(
    'text-left px-5 py-3.5 rounded-2xl border transition-all text-sm',
    selected ? 'bg-sage-soft border-sage text-ink' : 'bg-surface border-line text-ink-soft hover:border-sage/40 hover:text-ink',
  )

  return (
    <div className="min-h-screen bg-canvas flex items-center justify-center px-6 py-12">
      <div className="w-full max-w-lg">
        <div className="flex flex-col items-center mb-8">
          <Logo />
          <div className="flex gap-2 mt-6">
            {[1, 2, 3].map(s => <div key={s} className={clsx('h-1.5 w-14 rounded-full transition-all', s <= step ? 'bg-sage' : 'bg-line')} />)}
          </div>
        </div>

        <div className="card p-8 animate-fade-up">
          {step === 1 && (
            <div className="space-y-5">
              <div>
                <h2 className="text-2xl text-ink mb-1">Church Name</h2>
                <p className="text-sm text-ink-soft">How your church will appear across the dashboard and reports.</p>
              </div>
              <input value={form.name} onChange={e => update('name', e.target.value)} className="input" placeholder="Covenant Bible Church" autoFocus />
              <div className="grid grid-cols-2 gap-3">
                <input value={form.city} onChange={e => update('city', e.target.value)} className="input" placeholder="City" />
                <input value={form.state} onChange={e => update('state', e.target.value)} className="input" placeholder="State" />
              </div>
              <button onClick={() => setStep(2)} disabled={!form.name} className="btn-primary w-full">Continue</button>
            </div>
          )}

          {step === 2 && (
            <div className="space-y-5">
              <div>
                <h2 className="text-2xl text-ink mb-1">Congregation Size</h2>
                <p className="text-sm text-ink-soft">Used to compare you with similar-sized churches over time.</p>
              </div>
              <div className="space-y-2.5">
                {SIZE_OPTIONS.map(s => (
                  <button key={s} onClick={() => { update('size_range', s); setStep(3) }} className={clsx('w-full', choice(form.size_range === s))}>
                    {s} members
                  </button>
                ))}
              </div>
            </div>
          )}

          {step === 3 && (
            <div className="space-y-5">
              <div>
                <h2 className="text-2xl text-ink mb-1">Church Tradition</h2>
                <p className="text-sm text-ink-soft">Helps us frame your results in the right context.</p>
              </div>
              <div className="grid grid-cols-2 gap-2.5">
                {PROFILE_OPTIONS.map(p => (
                  <button key={p} onClick={() => update('theological_profile', p.toLowerCase())} className={choice(form.theological_profile === p.toLowerCase())}>
                    {p}
                  </button>
                ))}
              </div>
              <input value={form.denomination} onChange={e => update('denomination', e.target.value)} className="input" placeholder="Denomination (optional)" />
              <button onClick={() => mutation.mutate()} disabled={!form.theological_profile || mutation.isPending} className="btn-primary w-full">
                {mutation.isPending ? 'Setting things up…' : 'Finish Setup'}
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
