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
    <AuthShell title="Verify Email" subtitle="Confirming your address">
      <div className="text-center space-y-4">
        {state === 'pending' && <p className="text-ink-soft text-sm">Verifying your email…</p>}
        {state === 'ok' && (
          <>
            <div className="w-12 h-12 rounded-full bg-sage-soft text-sage-dark text-2xl flex items-center justify-center mx-auto">✓</div>
            <p className="text-ink text-sm">Your email is verified.</p>
            <Link to="/login" className="inline-block text-sage font-medium hover:text-sage-dark text-sm">Continue to sign in →</Link>
          </>
        )}
        {state === 'error' && (
          <>
            <p className="text-clay text-sm">This verification link is invalid or has expired.</p>
            <Link to="/login" className="inline-block text-sage font-medium hover:text-sage-dark text-sm">Back to sign in</Link>
          </>
        )}
      </div>
    </AuthShell>
  )
}
