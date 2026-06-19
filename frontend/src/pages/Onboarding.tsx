import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import { churchApi } from '../services/api'
import { useAuthStore } from '../hooks/useAuth'

const SIZE_OPTIONS = ['Under 100', '100–250', '250–500', '500–1000', '1000+']
const PROFILE_OPTIONS = ['Evangelical', 'Reformed', 'Baptist', 'Non-denominational', 'Charismatic', 'Anglican', 'Methodist', 'Lutheran', 'Other']

export default function OnboardingPage() {
  const navigate = useNavigate()
  const { setChurchId } = useAuthStore()
  const [step, setStep] = useState(1)
  const [form, setForm] = useState({
    name: '',
    denomination: '',
    size_range: '',
    city: '',
    state: '',
    theological_profile: '',
  })

  const mutation = useMutation({
    mutationFn: () => churchApi.create(form),
    onSuccess: (data) => {
      setChurchId(data.id)
      navigate('/admin')
    },
  })

  const update = (key: string, value: string) => setForm(f => ({ ...f, [key]: value }))

  return (
    <div className="min-h-screen bg-[#0A0C10] flex items-center justify-center px-6">
      <div className="w-full max-w-lg">
        {/* Header */}
        <div className="text-center mb-10">
          <div className="inline-flex items-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center font-bold" style={{ fontFamily: 'sans-serif' }}>B</div>
            <div className="text-left">
              <div className="text-lg font-semibold text-white" style={{ fontFamily: 'sans-serif', letterSpacing: '0.05em' }}>BHIS</div>
              <div className="text-[10px] text-white/40 tracking-widest uppercase" style={{ fontFamily: 'sans-serif' }}>Church Setup</div>
            </div>
          </div>
          {/* Progress */}
          <div className="flex gap-2 justify-center mt-4">
            {[1, 2, 3].map(s => (
              <div key={s} className={`h-1 w-16 rounded-full transition-all ${s <= step ? 'bg-blue-500' : 'bg-white/10'}`} />
            ))}
          </div>
        </div>

        <div className="bg-[#0F1117] rounded-2xl border border-white/8 p-8">
          {/* Step 1 — Church name */}
          {step === 1 && (
            <div className="space-y-5">
              <div>
                <h2 className="text-xl text-white/90 mb-1">What's the name of your church?</h2>
                <p className="text-sm text-white/40" style={{ fontFamily: 'sans-serif' }}>This is how it will appear in your dashboard and reports.</p>
              </div>
              <input
                value={form.name}
                onChange={e => update('name', e.target.value)}
                className="w-full bg-[#161920] border border-white/10 rounded-xl px-4 py-3 text-white text-sm focus:outline-none focus:border-blue-500/40"
                style={{ fontFamily: 'sans-serif' }}
                placeholder="Covenant Bible Church"
                autoFocus
              />
              <div className="grid grid-cols-2 gap-3">
                <input
                  value={form.city}
                  onChange={e => update('city', e.target.value)}
                  className="bg-[#161920] border border-white/10 rounded-xl px-4 py-3 text-white text-sm focus:outline-none focus:border-blue-500/40"
                  style={{ fontFamily: 'sans-serif' }}
                  placeholder="City"
                />
                <input
                  value={form.state}
                  onChange={e => update('state', e.target.value)}
                  className="bg-[#161920] border border-white/10 rounded-xl px-4 py-3 text-white text-sm focus:outline-none focus:border-blue-500/40"
                  style={{ fontFamily: 'sans-serif' }}
                  placeholder="State"
                />
              </div>
              <button
                onClick={() => setStep(2)}
                disabled={!form.name}
                className="w-full bg-blue-600 hover:bg-blue-500 disabled:opacity-40 text-white rounded-xl py-3 text-sm font-medium transition-colors"
                style={{ fontFamily: 'sans-serif' }}
              >
                Continue →
              </button>
            </div>
          )}

          {/* Step 2 — Church size */}
          {step === 2 && (
            <div className="space-y-5">
              <div>
                <h2 className="text-xl text-white/90 mb-1">How large is your congregation?</h2>
                <p className="text-sm text-white/40" style={{ fontFamily: 'sans-serif' }}>Used for benchmark comparisons with similar-sized churches.</p>
              </div>
              <div className="space-y-2">
                {SIZE_OPTIONS.map(s => (
                  <button
                    key={s}
                    onClick={() => { update('size_range', s); setStep(3) }}
                    className={`w-full text-left px-5 py-3.5 rounded-xl border transition-all text-sm ${form.size_range === s ? 'bg-blue-600/20 border-blue-500/50 text-white' : 'bg-[#161920] border-white/8 text-white/60 hover:border-white/20 hover:text-white/80'}`}
                    style={{ fontFamily: 'sans-serif' }}
                  >
                    {s} members
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Step 3 — Theological profile */}
          {step === 3 && (
            <div className="space-y-5">
              <div>
                <h2 className="text-xl text-white/90 mb-1">How would you describe your church?</h2>
                <p className="text-sm text-white/40" style={{ fontFamily: 'sans-serif' }}>Helps us contextualize your results appropriately.</p>
              </div>
              <div className="grid grid-cols-2 gap-2">
                {PROFILE_OPTIONS.map(p => (
                  <button
                    key={p}
                    onClick={() => update('theological_profile', p.toLowerCase())}
                    className={`text-left px-4 py-3 rounded-xl border transition-all text-sm ${form.theological_profile === p.toLowerCase() ? 'bg-blue-600/20 border-blue-500/50 text-white' : 'bg-[#161920] border-white/8 text-white/60 hover:border-white/20 hover:text-white/80'}`}
                    style={{ fontFamily: 'sans-serif' }}
                  >
                    {p}
                  </button>
                ))}
              </div>
              <input
                value={form.denomination}
                onChange={e => update('denomination', e.target.value)}
                className="w-full bg-[#161920] border border-white/10 rounded-xl px-4 py-3 text-white text-sm focus:outline-none focus:border-blue-500/40"
                style={{ fontFamily: 'sans-serif' }}
                placeholder="Denomination (optional)"
              />
              <button
                onClick={() => mutation.mutate()}
                disabled={!form.theological_profile || mutation.isPending}
                className="w-full bg-blue-600 hover:bg-blue-500 disabled:opacity-40 text-white rounded-xl py-3 text-sm font-medium transition-colors"
                style={{ fontFamily: 'sans-serif' }}
              >
                {mutation.isPending ? 'Creating your church...' : 'Finish Setup →'}
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
