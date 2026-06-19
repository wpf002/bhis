import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { authApi } from '../services/api'
import { useAuthStore } from '../hooks/useAuth'
import { AuthShell, Field, SubmitButton, FormError } from '../components/auth'

export default function LoginPage() {
  const navigate = useNavigate()
  const { setAuth, setChurchId } = useAuthStore()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true); setError('')
    try {
      const data = await authApi.login({ email, password })
      setAuth({ accessToken: data.access_token, refreshToken: data.refresh_token, userId: data.user_id, role: data.role })
      // Learn the church the user belongs to (needed for the dashboard).
      const me = await authApi.me()
      if (me.church_id) {
        setChurchId(me.church_id)
        navigate('/dashboard')
      } else {
        navigate('/onboarding')
      }
    } catch {
      setError('Invalid email or password')
    } finally {
      setLoading(false)
    }
  }

  return (
    <AuthShell subtitle="Sign in to your account">
      <form onSubmit={handleLogin} className="space-y-5">
        <Field label="Email" type="email" value={email} onChange={setEmail} placeholder="pastor@yourchurch.com" required autoFocus />
        <Field label="Password" type="password" value={password} onChange={setPassword} placeholder="••••••••" required />
        <div className="text-right -mt-2">
          <Link to="/forgot-password" className="text-xs text-white/40 hover:text-white/70" style={{ fontFamily: 'sans-serif' }}>Forgot password?</Link>
        </div>
        <FormError message={error} />
        <SubmitButton loading={loading} label="Sign In" />
      </form>
      <p className="text-center text-xs text-white/30 mt-6" style={{ fontFamily: 'sans-serif' }}>
        New to BHIS? <Link to="/register" className="text-blue-400 hover:text-blue-300">Create an account</Link>
      </p>
    </AuthShell>
  )
}
