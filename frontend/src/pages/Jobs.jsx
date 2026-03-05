import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api } from '../api'

export default function Jobs() {
  const [jobs, setJobs] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const navigate = useNavigate()

  const load = () => api.listJobs().then(setJobs).catch(e => setError(e.message)).finally(() => setLoading(false))

  useEffect(() => { load() }, [])

  const handleDelete = async (id, name) => {
    if (!confirm(`Delete job "${name}"?`)) return
    try { await api.deleteJob(id); load() } catch (e) { setError(e.message) }
  }

  return (
    <div>
      <div className="page-header">
        <h1>Jobs</h1>
        <Link to="/jobs/new"><button className="btn-primary">+ New Job</button></Link>
      </div>

      {error && <div className="error-msg">{error}</div>}

      {loading ? <p style={{ color: 'var(--text-muted)' }}>Loading…</p> : (
        <div className="card">
          {jobs.length === 0 ? (
            <p className="empty">No jobs yet. <Link to="/jobs/new">Create your first job.</Link></p>
          ) : (
            <table>
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Handler Type</th>
                  <th>Validation</th>
                  <th>Concurrency</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {jobs.map(j => (
                  <tr key={j.id}>
                    <td>
                      <div style={{ fontWeight: 500 }}>{j.name}</div>
                      {j.description && <div style={{ color: 'var(--text-muted)', fontSize: 12 }}>{j.description}</div>}
                    </td>
                    <td className="mono">{j.handler_config?.type || '—'}</td>
                    <td>
                      {j.input_validation_enabled && <span style={{ color: 'var(--success)', fontSize: 12, marginRight: 6 }}>✓ Input</span>}
                      {j.output_validation_enabled && <span style={{ color: 'var(--success)', fontSize: 12 }}>✓ Output</span>}
                      {!j.input_validation_enabled && !j.output_validation_enabled && <span style={{ color: 'var(--text-muted)', fontSize: 12 }}>none</span>}
                    </td>
                    <td style={{ color: j.concurrency_enabled ? 'var(--success)' : 'var(--text-muted)', fontSize: 13 }}>
                      {j.concurrency_enabled ? 'enabled' : 'disabled'}
                    </td>
                    <td>
                      <div style={{ display: 'flex', gap: 8 }}>
                        <Link to={`/jobs/${j.id}/edit`}><button className="btn-secondary btn-sm">Edit</button></Link>
                        <button className="btn-danger btn-sm" onClick={() => handleDelete(j.id, j.name)}>Delete</button>
                      </div>
                    </td>
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
