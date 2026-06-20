import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { surveyApi, scoringApi, churchApi } from '../services/api'
import { useAuthStore } from '../hooks/useAuth'
import { Logo } from '../components/ui'

function CopyField({ label, value }: { label: string; value: string }) {
  const [copied, setCopied] = useState(false)
  const copy = async () => {
    try { await navigator.clipboard.writeText(value); setCopied(true); setTimeout(() => setCopied(false), 1500) } catch { /* noop */ }
  }
  return (
    <div>
      <label className="label">{label}</label>
      <div className="flex gap-2">
        <input readOnly value={value} className="input flex-1 text-xs" />
        <button onClick={copy} className="btn-primary px-4 py-2">{copied ? 'Copied ✓' : 'Copy'}</button>
      </div>
    </div>
  )
}

export default function AdminPage() {
  const qc = useQueryClient()
  const { churchId } = useAuthStore()
  const [cycle, setCycle] = useState('Spring 2026')
  const [instanceId, setInstanceId] = useState('')
  const [message, setMessage] = useState('')
  const [inviteUrl, setInviteUrl] = useState('')

  const { data: templates = [] } = useQuery({ queryKey: ['templates'], queryFn: surveyApi.getTemplates })

  const createMutation = useMutation({
    mutationFn: (templateId: string) => surveyApi.createInstance({ template_id: templateId, assessment_cycle: cycle }),
    onSuccess: (data) => { setInstanceId(data.id); setMessage('Survey created. Launch it, then share the link below.'); qc.invalidateQueries({ queryKey: ['templates'] }) },
  })
  const launchMutation = useMutation({ mutationFn: (id: string) => surveyApi.launch(id), onSuccess: () => setMessage('Survey launched. Your congregation can now respond.') })
  const closeMutation = useMutation({ mutationFn: (id: string) => surveyApi.close(id), onSuccess: () => setMessage('Survey closed. No new responses will be accepted.') })
  const aggregateMutation = useMutation({ mutationFn: (id: string) => scoringApi.aggregateChurch(id), onSuccess: (d: any) => setMessage(`Results refreshed. Overall health: ${d.health_score}.`) })
  const inviteMutation = useMutation({
    mutationFn: () => churchApi.createInvite(churchId!, { role: 'leader' }),
    onSuccess: (d) => setInviteUrl(`${window.location.origin}/join/${d.token}`),
  })

  const memberLink = instanceId ? `${window.location.origin}/survey/${instanceId}` : ''

  return (
    <div className="min-h-screen bg-canvas">
      <header className="border-b border-line bg-surface/80 backdrop-blur">
        <div className="max-w-3xl mx-auto px-6 py-4 flex items-center justify-between">
          <Logo />
          <Link to="/dashboard" className="text-sm text-ink-soft hover:text-ink">← Dashboard</Link>
        </div>
      </header>

      <div className="max-w-3xl mx-auto px-6 py-8">
        <h1 className="text-3xl text-ink mb-1">Survey Management</h1>
        <p className="text-ink-soft mb-8">Send a survey to your congregation, then review the results.</p>

        {message && (
          <div className="mb-6 rounded-2xl bg-sage-soft border border-sage/25 px-4 py-3 text-sm text-sage-dark">{message}</div>
        )}

        <div className="card p-6 mb-4">
          <h2 className="text-lg text-ink mb-4">How It Works</h2>
          <ol className="space-y-2 text-sm text-ink-soft">
            <li>1. Create a survey.</li>
            <li>2. Launch it.</li>
            <li>3. Copy the survey link and share it with your congregation.</li>
            <li>4. View results on your dashboard as people respond.</li>
          </ol>
        </div>

        <div className="card p-6 mb-4">
          <h2 className="text-lg text-ink mb-4">Create a Survey</h2>
          <div className="space-y-4">
            <div>
              <label className="label">Season Label</label>
              <input value={cycle} onChange={e => setCycle(e.target.value)} className="input" placeholder="Spring 2026" />
            </div>
            {templates.map((t: any) => (
              <div key={t.id} className="flex items-center justify-between gap-4 p-4 bg-warmth rounded-2xl border border-line">
                <div>
                  <div className="text-sm text-ink">{t.name}</div>
                  <div className="text-xs text-ink-faint mt-0.5">{t.question_count} questions · about {t.estimated_minutes} min</div>
                </div>
                <button onClick={() => createMutation.mutate(t.id)} disabled={createMutation.isPending} className="btn-primary px-4 py-2">Create</button>
              </div>
            ))}
          </div>
        </div>

        <div className="card p-6 mb-4 space-y-4">
          <h2 className="text-lg text-ink">Manage a Survey</h2>
          <input value={instanceId} onChange={e => setInstanceId(e.target.value)} className="input" placeholder="Survey ID (filled in after you create one)" />
          <div className="flex flex-wrap gap-3">
            <button onClick={() => launchMutation.mutate(instanceId)} disabled={!instanceId} className="btn-primary flex-1 min-w-28">Launch</button>
            <button onClick={() => closeMutation.mutate(instanceId)} disabled={!instanceId} className="btn-ghost flex-1 min-w-28">Close</button>
            <button onClick={() => aggregateMutation.mutate(instanceId)} disabled={!instanceId} className="btn-ghost flex-1 min-w-28">Refresh Results</button>
          </div>
          {memberLink && <CopyField label="Share this link with your congregation (no login needed)" value={memberLink} />}
        </div>

        <div className="card p-6 space-y-4">
          <h2 className="text-lg text-ink">Invite a Co-Leader</h2>
          <p className="text-sm text-ink-soft">Generate a single-use link for another leader to join your dashboard.</p>
          <button onClick={() => inviteMutation.mutate()} disabled={!churchId || inviteMutation.isPending} className="btn-primary">Generate Invite Link</button>
          {inviteUrl && <CopyField label="Co-leader invite link" value={inviteUrl} />}
        </div>
      </div>
    </div>
  )
}
