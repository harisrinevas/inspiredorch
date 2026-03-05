import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api'
import StatusBadge from '../components/StatusBadge'

export default function Runs() {
  const [runs, setRuns] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const load = () => api.listRuns().then(setRuns).catch(e => setError(e.message)).finally(() => setLoading(false))

  useEffect(() => { load() }, [])

  return (
    <div>
      <div className="page-header">
        <h1>Runs</h1>
        <button className="btn-secondary" onClick={load}>Refresh</button>
      </div>

      {error && <div className="error-msg">{error}</div>}

      {loading ? <p style={{ color: 'var(--text-muted)' }}>Loading…</p> : (
        <div className="card">
          {runs.length === 0 ? (
            <p className="empty">No runs yet. <Link to="/dags">Trigger a run from a DAG.</Link></p>
          ) : (
            <table>
              <thead>
                <tr>
                  <th>Run ID</th>
                  <th>DAG ID</th>
                  <th>Status</th>
                  <th>Triggered By</th>
                  <th>Time</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {runs.map(r => (
                  <tr key={r.id}>
                    <td><Link to={`/runs/${r.id}`} className="mono">{r.id.slice(0, 12)}…</Link></td>
                    <td className="mono">{r.dag_id.slice(0, 12)}…</td>
                    <td><StatusBadge status={r.status} /></td>
                    <td style={{ color: 'var(--text-muted)' }}>{r.triggered_by || '—'}</td>
                    <td style={{ color: 'var(--text-muted)' }}>{new Date(r.trigger_time).toLocaleString()}</td>
                    <td><Link to={`/runs/${r.id}`}><button className="btn-secondary btn-sm">View</button></Link></td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}
    </div>
  )
}
