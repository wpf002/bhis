import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { authApi } from '../services/api'
import { useAuthStore } from '../hooks/useAuth'
import { AuthShell, Field, SubmitButton, FormError } from '../components/auth'

export default function RegisterPage() {
  const navigate = useNavigate()
  const { setAuth } = useAuthStore()
  const [form, setForm] = useState({ email: '', password: '', first_name: '', last_name: '' })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const set = (k: string, v: string) => setForm(f => ({ ...f, [k]: v }))

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true); setError('')
    try {
      const data = await authApi.register({ ...form, role: 'admin' })
      setAuth({ accessToken: data.access_token, refreshToken: data.refresh_token, userId: data.user_id, role: data.role })
      navigate('/onboarding')
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Could not create account')
    } finally {
      setLoading(false)
    }
  }

  return (
    <AuthShell subtitle="Create your church account">
      <form onSubmit={submit} className="space-y-5">
        <div className="grid grid-cols-2 gap-3">
          <Field label="First name" value={form.first_name} onChange={v => set('first_name', v)} required autoFocus />
          <Field label="Last name" value={form.last_name} onChange={v => set('last_name', v)} required />
        </div>
        <Field label="Email" type="email" value={form.email} onChange={v => set('email', v)} placeholder="pastor@yourchurch.com" required />
        <Field label="Password" type="password" value={form.password} onChange={v => set('password', v)} placeholder="At least 8 characters" required />
        <FormError message={error} />
        <SubmitButton loading={loading} label="Create Account" />
      </form>
      <p className="text-center text-xs text-white/30 mt-6" style={{ fontFamily: 'sans-serif' }}>
        Already have an account? <Link to="/login" className="text-blue-400 hover:text-blue-300">Sign in</Link>
      </p>
    </AuthShell>
  )
}
