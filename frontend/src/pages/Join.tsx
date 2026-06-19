import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { authApi } from '../services/api'
import { useAuthStore } from '../hooks/useAuth'
import { AuthShell, Field, SubmitButton, FormError } from '../components/auth'

export default function JoinPage() {
  const { inviteToken } = useParams<{ inviteToken: string }>()
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
      const data = await authApi.registerViaInvite({ token: inviteToken!, ...form })
      setAuth({ accessToken: data.access_token, refreshToken: data.refresh_token, userId: data.user_id, role: data.role })
      navigate('/dashboard')
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'This invite is invalid or has expired.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <AuthShell subtitle="You've been invited to join a church on BHIS">
      <form onSubmit={submit} className="space-y-5">
        <div className="grid grid-cols-2 gap-3">
          <Field label="First name" value={form.first_name} onChange={v => set('first_name', v)} required autoFocus />
          <Field label="Last name" value={form.last_name} onChange={v => set('last_name', v)} required />
        </div>
        <Field label="Email" type="email" value={form.email} onChange={v => set('email', v)} placeholder="you@yourchurch.com" required />
        <Field label="Password" type="password" value={form.password} onChange={v => set('password', v)} placeholder="At least 8 characters" required />
        <FormError message={error} />
        <SubmitButton loading={loading} label="Accept invite & continue" />
      </form>
    </AuthShell>
  )
}
