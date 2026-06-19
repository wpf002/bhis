import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { surveyApi, scoringApi, churchApi } from '../services/api'
import { useAuthStore } from '../hooks/useAuth'

function CopyField({ label, value }: { label: string; value: string }) {
  const [copied, setCopied] = useState(false)
  const copy = async () => {
    try { await navigator.clipboard.writeText(value); setCopied(true); setTimeout(() => setCopied(false), 1500) } catch { /* noop */ }
  }
  return (
    <div>
      <label className="block text-xs text-white/40 uppercase tracking-widest mb-2" style={{ fontFamily: 'sans-serif' }}>{label}</label>
      <div className="flex gap-2">
        <input readOnly value={value} className="flex-1 bg-[#161920] border border-white/10 rounded-xl px-4 py-2.5 text-white/70 text-xs" style={{ fontFamily: 'sans-serif' }} />
        <button onClick={copy} className="bg-blue-600 hover:bg-blue-500 text-white px-4 rounded-xl text-xs font-medium" style={{ fontFamily: 'sans-serif' }}>{copied ? 'Copied ✓' : 'Copy'}</button>
      </div>
    </div>
  )
}

export default function AdminPage() {
  const qc = useQueryClient()
  const { churchId } = useAuthStore()
  const [cycle, setCycle] = useState('Q1-2026')
  const [instanceId, setInstanceId] = useState('')
  const [message, setMessage] = useState('')
  const [inviteUrl, setInviteUrl] = useState('')

  const { data: templates = [] } = useQuery({ queryKey: ['templates'], queryFn: surveyApi.getTemplates })

  const createMutation = useMutation({
    mutationFn: (templateId: string) => surveyApi.createInstance({ template_id: templateId, assessment_cycle: cycle }),
    onSuccess: (data) => { setInstanceId(data.id); setMessage('Survey created. Launch it, then share the member link below.'); qc.invalidateQueries({ queryKey: ['templates'] }) },
  })
  const launchMutation = useMutation({ mutationFn: (id: string) => surveyApi.launch(id), onSuccess: () => setMessage('Survey launched — members can now take the assessment.') })
  const closeMutation = useMutation({ mutationFn: (id: string) => surveyApi.close(id), onSuccess: () => setMessage('Survey closed — no new responses will be accepted.') })
  const aggregateMutation = useMutation({ mutationFn: (id: string) => scoringApi.aggregateChurch(id), onSuccess: (d: any) => setMessage(`Aggregation complete. Health score: ${d.health_score}`) })
  const inviteMutation = useMutation({
    mutationFn: () => churchApi.createInvite(churchId!, { role: 'leader' }),
    onSuccess: (d) => setInviteUrl(`${window.location.origin}/join/${d.token}`),
  })

  const memberLink = instanceId ? `${window.location.origin}/survey/${instanceId}` : ''

  return (
    <div className="min-h-screen bg-[#0A0C10] text-white p-8" style={{ fontFamily: 'Georgia, serif' }}>
      <div className="max-w-3xl mx-auto">
        <div className="mb-8 flex items-center justify-between">
          <div>
            <div className="text-[10px] text-white/30 uppercase tracking-widest mb-1" style={{ fontFamily: 'sans-serif' }}>BHIS Admin</div>
            <h1 className="text-2xl text-white/90">Survey Management</h1>
          </div>
          <Link to="/dashboard" className="text-xs text-white/40 hover:text-white/70" style={{ fontFamily: 'sans-serif' }}>← Dashboard</Link>
        </div>

        {message && (
          <div className="mb-6 p-4 rounded-xl bg-blue-500/15 border border-blue-500/30 text-blue-300 text-sm" style={{ fontFamily: 'sans-serif' }}>{message}</div>
        )}

        {/* Next steps */}
        <div className="bg-[#0F1117] rounded-2xl border border-white/8 p-6 mb-4">
          <h2 className="text-lg text-white/80 mb-4">Get your congregation assessed</h2>
          <ol className="space-y-2 text-sm text-white/60" style={{ fontFamily: 'sans-serif' }}>
            <li>1. Create a survey for this cycle.</li>
            <li>2. Launch it.</li>
            <li>3. Copy the member link and share it with your congregation.</li>
            <li>4. Once you have enough responses, view results on the dashboard.</li>
          </ol>
        </div>

        {/* Create Survey */}
        <div className="bg-[#0F1117] rounded-2xl border border-white/8 p-6 mb-4">
          <h2 className="text-lg text-white/80 mb-4">Create Survey Instance</h2>
          <div className="space-y-4">
            <div>
              <label className="block text-xs text-white/40 uppercase tracking-widest mb-2" style={{ fontFamily: 'sans-serif' }}>Assessment Cycle Label</label>
              <input value={cycle} onChange={e => setCycle(e.target.value)} className="w-full bg-[#161920] border border-white/10 rounded-xl px-4 py-3 text-white text-sm focus:outline-none focus:border-blue-500/40" style={{ fontFamily: 'sans-serif' }} placeholder="Q1-2026" />
            </div>
            {templates.map((t: any) => (
              <div key={t.id} className="flex items-center justify-between p-4 bg-[#161920] rounded-xl border border-white/6">
                <div>
                  <div className="text-sm text-white/80">{t.name}</div>
                  <div className="text-xs text-white/40 mt-0.5" style={{ fontFamily: 'sans-serif' }}>v{t.version} · {t.question_count} questions · ~{t.estimated_minutes} min</div>
                </div>
                <button onClick={() => createMutation.mutate(t.id)} disabled={createMutation.isPending} className="bg-blue-600 hover:bg-blue-500 disabled:opacity-40 text-white px-4 py-2 rounded-lg text-xs font-medium" style={{ fontFamily: 'sans-serif' }}>Create</button>
              </div>
            ))}
          </div>
        </div>

        {/* Instance actions */}
        <div className="bg-[#0F1117] rounded-2xl border border-white/8 p-6 mb-4 space-y-4">
          <h2 className="text-lg text-white/80">Instance Actions</h2>
          <input value={instanceId} onChange={e => setInstanceId(e.target.value)} className="w-full bg-[#161920] border border-white/10 rounded-xl px-4 py-3 text-white text-sm focus:outline-none focus:border-blue-500/40" style={{ fontFamily: 'sans-serif' }} placeholder="Survey instance ID (filled in after Create)" />
          <div className="flex flex-wrap gap-3" style={{ fontFamily: 'sans-serif' }}>
            <button onClick={() => launchMutation.mutate(instanceId)} disabled={!instanceId} className="flex-1 min-w-32 bg-emerald-700 hover:bg-emerald-600 disabled:opacity-40 text-white py-2.5 rounded-xl text-sm font-medium">Launch</button>
            <button onClick={() => closeMutation.mutate(instanceId)} disabled={!instanceId} className="flex-1 min-w-32 bg-white/10 hover:bg-white/15 disabled:opacity-40 text-white py-2.5 rounded-xl text-sm font-medium">Close</button>
            <button onClick={() => aggregateMutation.mutate(instanceId)} disabled={!instanceId} className="flex-1 min-w-32 bg-indigo-700 hover:bg-indigo-600 disabled:opacity-40 text-white py-2.5 rounded-xl text-sm font-medium">Aggregate</button>
          </div>
          {memberLink && <CopyField label="Member survey link (no login required)" value={memberLink} />}
        </div>

        {/* Invite a co-leader */}
        <div className="bg-[#0F1117] rounded-2xl border border-white/8 p-6 space-y-4">
          <h2 className="text-lg text-white/80">Invite a Co-Leader</h2>
          <p className="text-xs text-white/40" style={{ fontFamily: 'sans-serif' }}>Generate a single-use link for another leader to join your church's dashboard.</p>
          <button onClick={() => inviteMutation.mutate()} disabled={!churchId || inviteMutation.isPending} className="bg-blue-600 hover:bg-blue-500 disabled:opacity-40 text-white px-4 py-2.5 rounded-xl text-sm font-medium" style={{ fontFamily: 'sans-serif' }}>Generate invite link</button>
          {inviteUrl && <CopyField label="Co-leader invite link" value={inviteUrl} />}
        </div>
      </div>
    </div>
  )
}
