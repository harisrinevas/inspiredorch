import { useEffect, useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { api } from '../api'
import StatusBadge from '../components/StatusBadge'

export default function RunDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [run, setRun] = useState(null)
  const [error, setError] = useState(null)
  const [cancelling, setCancelling] = useState(false)

  const load = () => api.getRun(id).then(setRun).catch(e => setError(e.message))

  useEffect(() => {
    load()
    // Auto-refresh while run is active
    const interval = setInterval(() => {
      if (run && ['success', 'failed', 'cancelled'].includes(run.status)) return
      load()
    }, 3000)
    return () => clearInterval(interval)
  }, [id, run?.status])

  const handleCancel = async () => {
    setCancelling(true)
    try { await api.cancelRun(id); load() } catch (e) { setError(e.message) } finally { setCancelling(false) }
  }

  if (!run && !error) return <p style={{ color: 'var(--text-muted)' }}>Loading…</p>

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Run Detail</h1>
          <p className="mono" style={{ color: 'var(--text-muted)', marginTop: 4 }}>{id}</p>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <button className="btn-secondary" onClick={load}>Refresh</button>
          {run && ['pending', 'running'].includes(run.status) && (
            <button className="btn-danger" onClick={handleCancel} disabled={cancelling}>
              {cancelling ? 'Cancelling…' : 'Cancel Run'}
            </button>
          )}
        </div>
      </div>

      {error && <div className="error-msg">{error}</div>}

      {run && (
        <>
          <div className="card" style={{ marginBottom: 16 }}>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16 }}>
              <div>
                <div style={{ color: 'var(--text-muted)', fontSize: 12, marginBottom: 4 }}>STATUS</div>
                <StatusBadge status={run.status} />
              </div>
              <div>
                <div style={{ color: 'var(--text-muted)', fontSize: 12, marginBottom: 4 }}>DAG</div>
                <span className="mono">{run.dag_id.slice(0, 12)}…</span>
              </div>
              <div>
                <div style={{ color: 'var(--text-muted)', fontSize: 12, marginBottom: 4 }}>TRIGGERED BY</div>
                <span>{run.triggered_by || '—'}</span>
              </div>
              <div>
                <div style={{ color: 'var(--text-muted)', fontSize: 12, marginBottom: 4 }}>TIME</div>
                <span style={{ fontSize: 13 }}>{new Date(run.trigger_time).toLocaleString()}</span>
              </div>
            </div>
          </div>

          <div className="card">
            <h2 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16 }}>Job States ({run.job_run_states.length})</h2>
            {run.job_run_states.length === 0 ? (
              <p style={{ color: 'var(--text-muted)' }}>No job states found.</p>
            ) : (
              <table>
                <thead>
                  <tr>
                    <th>Job ID</th>
                    <th>Status</th>
                    <th>Started</th>
                    <th>Finished</th>
                    <th>Error</th>
                  </tr>
                </thead>
                <tbody>
                  {run.job_run_states.map(s => (
                    <tr key={s.id}>
                      <td className="mono">{s.job_id.slice(0, 12)}…</td>
                      <td><StatusBadge status={s.status} /></td>
                      <td style={{ color: 'var(--text-muted)', fontSize: 13 }}>
                        {s.started_at ? new Date(s.started_at).toLocaleTimeString() : '—'}
                      </td>
                      <td style={{ color: 'var(--text-muted)', fontSize: 13 }}>
                        {s.finished_at ? new Date(s.finished_at).toLocaleTimeString() : '—'}
                      </td>
                      <td style={{ color: 'var(--danger)', fontSize: 12, maxWidth: 300 }}>
                        {s.error_message ? (
                          <details>
                            <summary style={{ cursor: 'pointer' }}>View error</summary>
                            <pre style={{ whiteSpace: 'pre-wrap', marginTop: 4 }}>{s.error_message}</pre>
                          </details>
                        ) : '—'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </>
      )}
    </div>
  )
}
