import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { surveyApi, scoringApi } from '../services/api'
import clsx from 'clsx'

export default function AdminPage() {
  const qc = useQueryClient()
  const [cycle, setCycle] = useState('Q2-2024')
  const [message, setMessage] = useState('')

  const { data: templates = [] } = useQuery({
    queryKey: ['templates'],
    queryFn: surveyApi.getTemplates,
  })

  const createMutation = useMutation({
    mutationFn: (templateId: string) =>
      surveyApi.createInstance({ template_id: templateId, assessment_cycle: cycle }),
    onSuccess: (data) => {
      setMessage(`Survey instance created. ID: ${data.id}`)
      qc.invalidateQueries({ queryKey: ['templates'] })
    },
  })

  const launchMutation = useMutation({
    mutationFn: (instanceId: string) => surveyApi.launch(instanceId),
    onSuccess: () => setMessage('Survey launched — members can now take the assessment.'),
  })

  const aggregateMutation = useMutation({
    mutationFn: (instanceId: string) => scoringApi.aggregateChurch(instanceId),
    onSuccess: (data) => setMessage(`Aggregation complete. Health score: ${data.health_score}`),
  })

  return (
    <div className="min-h-screen bg-[#0A0C10] text-white p-8" style={{ fontFamily: 'Georgia, serif' }}>
      <div className="max-w-3xl mx-auto">
        <div className="mb-8">
          <div className="text-[10px] text-white/30 uppercase tracking-widest mb-1" style={{ fontFamily: 'sans-serif' }}>BHIS Admin</div>
          <h1 className="text-2xl text-white/90">Survey Management</h1>
        </div>

        {message && (
          <div className="mb-6 p-4 rounded-xl bg-blue-500/15 border border-blue-500/30 text-blue-300 text-sm" style={{ fontFamily: 'sans-serif' }}>
            {message}
          </div>
        )}

        {/* Create Survey */}
        <div className="bg-[#0F1117] rounded-2xl border border-white/8 p-6 mb-4">
          <h2 className="text-lg text-white/80 mb-4">Create Survey Instance</h2>
          <div className="space-y-4">
            <div>
              <label className="block text-xs text-white/40 uppercase tracking-widest mb-2" style={{ fontFamily: 'sans-serif' }}>Assessment Cycle Label</label>
              <input
                value={cycle}
                onChange={e => setCycle(e.target.value)}
                className="w-full bg-[#161920] border border-white/10 rounded-xl px-4 py-3 text-white text-sm focus:outline-none focus:border-blue-500/40"
                style={{ fontFamily: 'sans-serif' }}
                placeholder="Q2-2024"
              />
            </div>
            {templates.map((t: any) => (
              <div key={t.id} className="flex items-center justify-between p-4 bg-[#161920] rounded-xl border border-white/6">
                <div>
                  <div className="text-sm text-white/80">{t.name}</div>
                  <div className="text-xs text-white/40 mt-0.5" style={{ fontFamily: 'sans-serif' }}>v{t.version} · {t.question_count} questions · ~{t.estimated_minutes} min</div>
                </div>
                <button
                  onClick={() => createMutation.mutate(t.id)}
                  disabled={createMutation.isPending}
                  className="bg-blue-600 hover:bg-blue-500 disabled:opacity-40 text-white px-4 py-2 rounded-lg text-xs font-medium transition-colors"
                  style={{ fontFamily: 'sans-serif' }}
                >
                  Create Instance
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* Actions on existing instance */}
        <div className="bg-[#0F1117] rounded-2xl border border-white/8 p-6 mb-4">
          <h2 className="text-lg text-white/80 mb-2">Instance Actions</h2>
          <p className="text-xs text-white/40 mb-4" style={{ fontFamily: 'sans-serif' }}>Enter an instance ID from the step above</p>
          <InstanceActions
            onLaunch={(id) => launchMutation.mutate(id)}
            onAggregate={(id) => aggregateMutation.mutate(id)}
            loading={launchMutation.isPending || aggregateMutation.isPending}
          />
        </div>

        {/* Workflow guide */}
        <div className="bg-[#0F1117] rounded-2xl border border-white/8 p-6">
          <h2 className="text-lg text-white/80 mb-4">Full Workflow</h2>
          <div className="space-y-3">
            {[
              { step: '1', label: 'Create Instance', desc: 'Creates a survey for your church for this cycle.' },
              { step: '2', label: 'Launch', desc: 'Sets status to active. Members can now take the survey.' },
              { step: '3', label: 'Distribute Survey Link', desc: 'Share /survey/{instanceId} with your congregation.' },
              { step: '4', label: 'Wait for Responses', desc: 'Minimum 20 responses for meaningful data. More is better.' },
              { step: '5', label: 'Run Aggregation', desc: 'Calculates church-level scores, archetype, and drift.' },
              { step: '6', label: 'View Dashboard', desc: 'Check /dashboard to see results, recommendations, and insights.' },
            ].map(w => (
              <div key={w.step} className="flex gap-4 items-start">
                <div className="w-6 h-6 rounded-full bg-blue-500/20 border border-blue-500/30 flex items-center justify-center text-blue-400 text-xs font-bold flex-shrink-0" style={{ fontFamily: 'sans-serif' }}>{w.step}</div>
                <div>
                  <div className="text-sm text-white/70">{w.label}</div>
                  <div className="text-xs text-white/35 mt-0.5" style={{ fontFamily: 'sans-serif' }}>{w.desc}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

function InstanceActions({ onLaunch, onAggregate, loading }: {
  onLaunch: (id: string) => void
  onAggregate: (id: string) => void
  loading: boolean
}) {
  const [instanceId, setInstanceId] = useState('')
  return (
    <div className="space-y-3">
      <input
        value={instanceId}
        onChange={e => setInstanceId(e.target.value)}
        className="w-full bg-[#161920] border border-white/10 rounded-xl px-4 py-3 text-white text-sm focus:outline-none focus:border-blue-500/40"
        style={{ fontFamily: 'sans-serif' }}
        placeholder="Paste instance UUID here"
      />
      <div className="flex gap-3">
        <button
          onClick={() => onLaunch(instanceId)}
          disabled={!instanceId || loading}
          className="flex-1 bg-emerald-700 hover:bg-emerald-600 disabled:opacity-40 text-white py-2.5 rounded-xl text-sm font-medium transition-colors"
          style={{ fontFamily: 'sans-serif' }}
        >
          Launch Survey
        </button>
        <button
          onClick={() => onAggregate(instanceId)}
          disabled={!instanceId || loading}
          className="flex-1 bg-indigo-700 hover:bg-indigo-600 disabled:opacity-40 text-white py-2.5 rounded-xl text-sm font-medium transition-colors"
          style={{ fontFamily: 'sans-serif' }}
        >
          Run Aggregation
        </button>
      </div>
    </div>
  )
}
