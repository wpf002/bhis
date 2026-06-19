import { useEffect, useState } from 'react'
import { useSearchParams, Link } from 'react-router-dom'
import { authApi } from '../services/api'
import { AuthShell } from '../components/auth'

export default function VerifyEmailPage() {
  const [params] = useSearchParams()
  const token = params.get('token')
  const [state, setState] = useState<'pending' | 'ok' | 'error'>('pending')

  useEffect(() => {
    if (!token) { setState('error'); return }
    authApi.verifyEmail(token).then(() => setState('ok')).catch(() => setState('error'))
  }, [token])

  return (
    <AuthShell subtitle="Email verification">
      <div className="text-center space-y-4" style={{ fontFamily: 'sans-serif' }}>
        {state === 'pending' && <p className="text-white/60 text-sm">Verifying your email…</p>}
        {state === 'ok' && (
          <>
            <div className="text-emerald-400 text-2xl">✓</div>
            <p className="text-white/80 text-sm">Your email is verified.</p>
            <Link to="/login" className="inline-block text-blue-400 hover:text-blue-300 text-sm">Continue to sign in →</Link>
          </>
        )}
        {state === 'error' && (
          <>
            <p className="text-red-400 text-sm">This verification link is invalid or has expired.</p>
            <Link to="/login" className="inline-block text-blue-400 hover:text-blue-300 text-sm">Back to sign in</Link>
          </>
        )}
      </div>
    </AuthShell>
  )
}
