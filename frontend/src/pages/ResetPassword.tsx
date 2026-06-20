import { useState } from 'react'
import { useSearchParams, useNavigate, Link } from 'react-router-dom'
import { authApi } from '../services/api'
import { AuthShell, Field, SubmitButton, FormError } from '../components/auth'

export default function ResetPasswordPage() {
  const [params] = useSearchParams()
  const navigate = useNavigate()
  const token = params.get('token') || ''
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true); setError('')
    try {
      await authApi.resetPassword(token, password)
      navigate('/login')
    } catch {
      setError('This reset link is invalid or has expired.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <AuthShell title="New Password" subtitle="Choose a password to finish resetting">
      {token ? (
        <form onSubmit={submit} className="space-y-5">
          <Field label="New password" type="password" value={password} onChange={setPassword} placeholder="At least 8 characters" required autoFocus />
          <FormError message={error} />
          <SubmitButton loading={loading} label="Reset password" />
        </form>
      ) : (
        <p className="text-clay text-sm text-center">This reset link is missing its token.</p>
      )}
      <p className="text-center text-sm text-ink-soft mt-6">
        <Link to="/login" className="text-sage font-medium hover:text-sage-dark">Back to sign in</Link>
      </p>
    </AuthShell>
  )
}
