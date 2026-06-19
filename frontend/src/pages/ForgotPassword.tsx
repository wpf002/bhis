import { useState } from 'react'
import { Link } from 'react-router-dom'
import { authApi } from '../services/api'
import { AuthShell, Field, SubmitButton, FormNote } from '../components/auth'

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState('')
  const [sent, setSent] = useState(false)
  const [loading, setLoading] = useState(false)

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try { await authApi.forgotPassword(email) } finally { setLoading(false); setSent(true) }
  }

  return (
    <AuthShell subtitle="Reset your password">
      {sent ? (
        <FormNote>If an account exists for {email}, a reset link is on its way.</FormNote>
      ) : (
        <form onSubmit={submit} className="space-y-5">
          <Field label="Email" type="email" value={email} onChange={setEmail} placeholder="pastor@yourchurch.com" required autoFocus />
          <SubmitButton loading={loading} label="Send reset link" />
        </form>
      )}
      <p className="text-center text-xs text-white/30 mt-6" style={{ fontFamily: 'sans-serif' }}>
        <Link to="/login" className="text-blue-400 hover:text-blue-300">Back to sign in</Link>
      </p>
    </AuthShell>
  )
}
