import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { api } from '../api'

export default function DAGForm() {
  const { id } = useParams()
  const isEdit = Boolean(id)
  const navigate = useNavigate()

  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [scheduleCron, setScheduleCron] = useState('')
  const [scheduleTimezone, setScheduleTimezone] = useState('UTC')
  const [retentionOverride, setRetentionOverride] = useState('')
  const [allJobs, setAllJobs] = useState([])
  const [selectedJobIds, setSelectedJobIds] = useState([])
  const [edges, setEdges] = useState([])
  const [fromJob, setFromJob] = useState('')
  const [toJob, setToJob] = useState('')
  const [error, setError] = useState(null)
  const [saving, setSaving] = useState(false)
  const [validation, setValidation] = useState(null)

  useEffect(() => {
    api.listJobs().then(setAllJobs).catch(e => setError(e.message))
    if (!isEdit) return
    api.getDag(id).then(d => {
      setName(d.name)
      setDescription(d.description || '')
      setScheduleCron(d.schedule_cron || '')
      setScheduleTimezone(d.schedule_timezone || 'UTC')
      setRetentionOverride(d.retention_days_override ? String(d.retention_days_override) : '')
      const edgeList = d.edges || []
      setEdges(edgeList)
      // Collect all job ids from edges
      const ids = new Set()
      edgeList.forEach(e => { ids.add(e.from_job_id); ids.add(e.to_job_id) })
      setSelectedJobIds([...ids])
    }).catch(e => setError(e.message))
  }, [id, isEdit])

  const toggleJob = (jobId) => {
    setSelectedJobIds(prev =>
      prev.includes(jobId) ? prev.filter(j => j !== jobId) : [...prev, jobId]
    )
    // Remove edges referencing removed job
    setEdges(prev => prev.filter(e => e.from_job_id !== jobId && e.to_job_id !== jobId))
  }

  const addEdge = () => {
    if (!fromJob || !toJob || fromJob === toJob) return
    if (edges.find(e => e.from_job_id === fromJob && e.to_job_id === toJob)) return
    setEdges(prev => [...prev, { from_job_id: fromJob, to_job_id: toJob }])
    setFromJob('')
    setToJob('')
    setValidation(null)
  }

  const removeEdge = (i) => setEdges(prev => prev.filter((_, idx) => idx !== i))

  const jobName = (jid) => allJobs.find(j => j.id === jid)?.name || jid.slice(0, 8)

  const handleValidate = async () => {
    if (!isEdit) { setValidation({ error: 'Save the DAG first to validate.' }); return }
    try {
      const r = await api.validateDag(id)
      setValidation(r)
    } catch (e) { setValidation({ error: e.message }) }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)
    setSaving(true)
    try {
      const payload = {
        name,
        description: description || null,
        job_ids: selectedJobIds,
        edges,
        schedule_cron: scheduleCron || null,
        schedule_timezone: scheduleTimezone || null,
        retention_days_override: retentionOverride ? parseInt(retentionOverride) : null,
      }
      if (isEdit) await api.updateDag(id, payload)
      else await api.createDag(payload)
      navigate('/dags')
    } catch (e) { setError(e.message) } finally { setSaving(false) }
  }

  const selectedJobs = allJobs.filter(j => selectedJobIds.includes(j.id))

  return (
    <div style={{ maxWidth: 800 }}>
      <div className="page-header">
        <h1>{isEdit ? 'Edit DAG' : 'New DAG'}</h1>
        {isEdit && <button className="btn-secondary" onClick={handleValidate}>Validate DAG</button>}
      </div>

      {error && <div className="error-msg">{error}</div>}
      {validation && (
        <div style={{
          background: validation.valid ? 'rgba(34,197,94,0.1)' : 'rgba(239,68,68,0.1)',
          border: `1px solid ${validation.valid ? 'var(--success)' : 'var(--danger)'}`,
          borderRadius: 'var(--radius)', padding: '12px 16px', marginBottom: 16, fontSize: 14,
          color: validation.valid ? 'var(--success)' : 'var(--danger)',
        }}>
          {validation.valid
            ? `✓ Valid — ${validation.execution_waves?.length} execution wave(s): ${validation.execution_waves?.map(w => `[${w.map(id => jobName(id)).join(', ')}]`).join(' → ')}`
            : `✗ Invalid: ${validation.error}`}
        </div>
      )}

      <form onSubmit={handleSubmit}>
        <div className="card" style={{ marginBottom: 16 }}>
          <h3 style={{ marginBottom: 16, fontSize: 15 }}>Basic Info</h3>
          <div className="form-group">
            <label>Name *</label>
            <input required value={name} onChange={e => setName(e.target.value)} placeholder="e.g. etl-pipeline" />
          </div>
          <div className="form-group">
            <label>Description</label>
            <input value={description} onChange={e => setDescription(e.target.value)} placeholder="Optional description" />
          </div>
        </div>

        <div className="card" style={{ marginBottom: 16 }}>
          <h3 style={{ marginBottom: 12, fontSize: 15 }}>Jobs in this DAG</h3>
          <p style={{ color: 'var(--text-muted)', fontSize: 13, marginBottom: 12 }}>Select which jobs are part of this pipeline.</p>
          {allJobs.length === 0 ? (
            <p style={{ color: 'var(--text-muted)', fontSize: 14 }}>No jobs available. <a href="/jobs/new">Create jobs first.</a></p>
          ) : (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: 8 }}>
              {allJobs.map(j => (
                <label key={j.id} style={{
                  display: 'flex', alignItems: 'center', gap: 8, padding: '8px 12px',
                  background: selectedJobIds.includes(j.id) ? 'rgba(99,102,241,0.1)' : 'var(--surface2)',
                  border: `1px solid ${selectedJobIds.includes(j.id) ? 'var(--accent)' : 'var(--border)'}`,
                  borderRadius: 'var(--radius)', cursor: 'pointer', fontSize: 13,
                }}>
                  <input type="checkbox" checked={selectedJobIds.includes(j.id)} onChange={() => toggleJob(j.id)} style={{ width: 'auto' }} />
                  {j.name}
                </label>
              ))}
            </div>
          )}
        </div>

        {selectedJobs.length >= 2 && (
          <div className="card" style={{ marginBottom: 16 }}>
            <h3 style={{ marginBottom: 12, fontSize: 15 }}>Dependencies (Edges)</h3>
            <p style={{ color: 'var(--text-muted)', fontSize: 13, marginBottom: 12 }}>
              A → B means A must succeed before B runs.
            </p>
            <div style={{ display: 'flex', gap: 8, marginBottom: 12, alignItems: 'center' }}>
              <select value={fromJob} onChange={e => setFromJob(e.target.value)} style={{ flex: 1 }}>
                <option value="">From job…</option>
                {selectedJobs.map(j => <option key={j.id} value={j.id}>{j.name}</option>)}
              </select>
              <span style={{ color: 'var(--text-muted)' }}>→</span>
              <select value={toJob} onChange={e => setToJob(e.target.value)} style={{ flex: 1 }}>
                <option value="">To job…</option>
                {selectedJobs.filter(j => j.id !== fromJob).map(j => <option key={j.id} value={j.id}>{j.name}</option>)}
              </select>
              <button type="button" className="btn-primary btn-sm" onClick={addEdge}>Add</button>
            </div>
            {edges.length === 0 ? (
              <p style={{ color: 'var(--text-muted)', fontSize: 13 }}>No edges — all selected jobs will run in parallel.</p>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                {edges.map((e, i) => (
                  <div key={i} style={{
                    display: 'flex', alignItems: 'center', gap: 8, padding: '6px 12px',
                    background: 'var(--surface2)', borderRadius: 'var(--radius)', fontSize: 13,
                  }}>
                    <span style={{ color: 'var(--accent)' }}>{jobName(e.from_job_id)}</span>
                    <span style={{ color: 'var(--text-muted)' }}>→</span>
                    <span style={{ color: 'var(--accent)' }}>{jobName(e.to_job_id)}</span>
                    <button type="button" className="btn-danger btn-sm" style={{ marginLeft: 'auto' }} onClick={() => removeEdge(i)}>×</button>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        <div className="card" style={{ marginBottom: 16 }}>
          <h3 style={{ marginBottom: 12, fontSize: 15 }}>Schedule (Optional)</h3>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
            <div className="form-group" style={{ marginBottom: 0 }}>
              <label>Cron Expression</label>
              <input value={scheduleCron} onChange={e => setScheduleCron(e.target.value)} placeholder="e.g. 0 * * * * (hourly)" />
            </div>
            <div className="form-group" style={{ marginBottom: 0 }}>
              <label>Timezone</label>
              <input value={scheduleTimezone} onChange={e => setScheduleTimezone(e.target.value)} placeholder="UTC" />
            </div>
          </div>
        </div>

        <div className="card" style={{ marginBottom: 24 }}>
          <h3 style={{ marginBottom: 12, fontSize: 15 }}>Retention Override</h3>
          <div className="form-group" style={{ marginBottom: 0 }}>
            <label>Retention days (leave blank to use global default)</label>
            <input type="number" min="1" value={retentionOverride} onChange={e => setRetentionOverride(e.target.value)} placeholder="e.g. 30" />
          </div>
        </div>

        <div style={{ display: 'flex', gap: 12 }}>
          <button type="submit" className="btn-primary" disabled={saving}>
            {saving ? 'Saving…' : isEdit ? 'Save Changes' : 'Create DAG'}
          </button>
          <button type="button" className="btn-secondary" onClick={() => navigate('/dags')}>Cancel</button>
        </div>
      </form>
    </div>
  )
}
