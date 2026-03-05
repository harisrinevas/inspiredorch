import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api'
import StatusBadge from '../components/StatusBadge'

export default function Dashboard() {
  const [runs, setRuns] = useState([])
  const [dags, setDags] = useState([])
  const [jobs, setJobs] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([api.listRuns(), api.listDags(), api.listJobs()])
      .then(([r, d, j]) => { setRuns(r); setDags(d); setJobs(j) })
      .finally(() => setLoading(false))
  }, [])

  const running = runs.filter(r => r.status === 'running').length
  const failed = runs.filter(r => r.status === 'failed').length
  const recent = runs.slice(0, 10)

  return (
    <div>
      <div className="page-header">
        <h1>Dashboard</h1>
      </div>

      {loading ? <p style={{ color: 'var(--text-muted)' }}>Loading…</p> : (
        <>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16, marginBottom: 32 }}>
            {[
              { label: 'Total Runs', value: runs.length, color: 'var(--text)' },
              { label: 'Running', value: running, color: 'var(--running)' },
              { label: 'Failed', value: failed, color: 'var(--danger)' },
              { label: 'DAGs', value: dags.length, color: 'var(--accent)' },
            ].map(({ label, value, color }) => (
              <div key={label} className="card" style={{ textAlign: 'center' }}>
                <div style={{ fontSize: 32, fontWeight: 700, color }}>{value}</div>
                <div style={{ color: 'var(--text-muted)', fontSize: 13, marginTop: 4 }}>{label}</div>
              </div>
            ))}
          </div>

          <div className="card">
            <h2 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16 }}>Recent Runs</h2>
            {recent.length === 0 ? (
              <p className="empty">No runs yet. <Link to="/dags">Create a DAG</Link> and trigger a run.</p>
            ) : (
              <table>
                <thead><tr><th>Run ID</th><th>DAG</th><th>Status</th><th>Triggered</th><th>Time</th></tr></thead>
                <tbody>
                  {recent.map(r => (
                    <tr key={r.id}>
                      <td><Link to={`/runs/${r.id}`} className="mono">{r.id.slice(0, 8)}…</Link></td>
                      <td className="mono">{r.dag_id.slice(0, 8)}…</td>
                      <td><StatusBadge status={r.status} /></td>
                      <td style={{ color: 'var(--text-muted)' }}>{r.triggered_by || '—'}</td>
                      <td style={{ color: 'var(--text-muted)' }}>{new Date(r.trigger_time).toLocaleString()}</td>
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
