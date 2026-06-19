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
    <AuthShell title="Reset your password" subtitle="We'll email you a link to set a new one">
      {sent ? (
        <FormNote>If an account exists for {email}, a reset link is on its way.</FormNote>
      ) : (
        <form onSubmit={submit} className="space-y-5">
          <Field label="Email" type="email" value={email} onChange={setEmail} placeholder="pastor@yourchurch.com" required autoFocus />
          <SubmitButton loading={loading} label="Send reset link" />
        </form>
      )}
      <p className="text-center text-sm text-ink-soft mt-6">
        <Link to="/login" className="text-sage font-medium hover:text-sage-dark">Back to sign in</Link>
      </p>
    </AuthShell>
  )
}
