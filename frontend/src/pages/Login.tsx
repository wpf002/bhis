import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { authApi } from '../services/api'
import { useAuthStore } from '../hooks/useAuth'

export default function LoginPage() {
  const navigate = useNavigate()
  const { setAuth } = useAuthStore()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    try {
      const data = await authApi.login({ email, password })
      setAuth({
        accessToken: data.access_token,
        refreshToken: data.refresh_token,
        userId: data.user_id,
        role: data.role,
      })
      navigate(data.role === 'respondent' ? '/survey' : '/dashboard')
    } catch {
      setError('Invalid email or password')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-[#0A0C10] flex items-center justify-center px-4">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-10">
          <div className="inline-flex items-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center text-sm font-bold" style={{ fontFamily: 'sans-serif' }}>B</div>
            <div className="text-left">
              <div className="text-lg font-semibold text-white" style={{ fontFamily: 'sans-serif', letterSpacing: '0.05em' }}>BHIS</div>
              <div className="text-[10px] text-white/40 tracking-widest uppercase" style={{ fontFamily: 'sans-serif' }}>Biblical Health Intelligence</div>
            </div>
          </div>
          <p className="text-white/40 text-sm" style={{ fontFamily: 'sans-serif' }}>Sign in to your account</p>
        </div>

        {/* Form */}
        <div className="bg-[#0F1117] rounded-2xl border border-white/8 p-8">
          <form onSubmit={handleLogin} className="space-y-5">
            <div>
              <label className="block text-xs text-white/50 uppercase tracking-widest mb-2" style={{ fontFamily: 'sans-serif' }}>Email</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full bg-[#161920] border border-white/10 rounded-xl px-4 py-3 text-white text-sm focus:outline-none focus:border-blue-500/50 transition-colors"
                style={{ fontFamily: 'sans-serif' }}
                placeholder="pastor@yourchurch.com"
                required
              />
            </div>
            <div>
              <label className="block text-xs text-white/50 uppercase tracking-widest mb-2" style={{ fontFamily: 'sans-serif' }}>Password</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full bg-[#161920] border border-white/10 rounded-xl px-4 py-3 text-white text-sm focus:outline-none focus:border-blue-500/50 transition-colors"
                style={{ fontFamily: 'sans-serif' }}
                placeholder="••••••••"
                required
              />
            </div>

            {error && (
              <div className="text-red-400 text-sm text-center" style={{ fontFamily: 'sans-serif' }}>{error}</div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white rounded-xl py-3 text-sm font-medium transition-colors"
              style={{ fontFamily: 'sans-serif' }}
            >
              {loading ? 'Signing in...' : 'Sign In'}
            </button>
          </form>
        </div>

        <p className="text-center text-xs text-white/20 mt-6" style={{ fontFamily: 'sans-serif' }}>
          Biblical Health Intelligence System · Secure Login
        </p>
      </div>
    </div>
  )
}
