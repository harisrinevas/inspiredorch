import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api'

export default function DAGs() {
  const [dags, setDags] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [triggering, setTriggering] = useState({})

  const load = () => api.listDags().then(setDags).catch(e => setError(e.message)).finally(() => setLoading(false))

  useEffect(() => { load() }, [])

  const handleDelete = async (id, name) => {
    if (!confirm(`Delete DAG "${name}"?`)) return
    try { await api.deleteDag(id); load() } catch (e) { setError(e.message) }
  }

  const handleTrigger = async (id) => {
    setTriggering(t => ({ ...t, [id]: true }))
    try {
      const run = await api.triggerRun(id, { triggered_by: 'manual' })
      alert(`Run triggered: ${run.id}`)
    } catch (e) {
      setError(e.message)
    } finally {
      setTriggering(t => ({ ...t, [id]: false }))
    }
  }

  const handlePause = async (dag) => {
    try { await api.updateDag(dag.id, { paused: !dag.paused }); load() } catch (e) { setError(e.message) }
  }

  return (
    <div>
      <div className="page-header">
        <h1>DAGs</h1>
        <Link to="/dags/new"><button className="btn-primary">+ New DAG</button></Link>
      </div>

      {error && <div className="error-msg">{error}</div>}

      {loading ? <p style={{ color: 'var(--text-muted)' }}>Loading…</p> : (
        <div className="card">
          {dags.length === 0 ? (
            <p className="empty">No DAGs yet. <Link to="/dags/new">Create your first pipeline.</Link></p>
          ) : (
            <table>
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Jobs</th>
                  <th>Schedule</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {dags.map(d => (
                  <tr key={d.id}>
                    <td>
                      <div style={{ fontWeight: 500 }}>{d.name}</div>
                      {d.description && <div style={{ color: 'var(--text-muted)', fontSize: 12 }}>{d.description}</div>}
                    </td>
                    <td style={{ color: 'var(--text-muted)' }}>{d.edges.length} edge{d.edges.length !== 1 ? 's' : ''}</td>
                    <td className="mono">{d.schedule_cron || <span style={{ color: 'var(--text-muted)' }}>manual</span>}</td>
                    <td>
                      <span style={{ color: d.paused ? 'var(--warning)' : 'var(--success)', fontSize: 13 }}>
                        {d.paused ? 'paused' : 'active'}
                      </span>
                    </td>
                    <td>
                      <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                        <button className="btn-primary btn-sm" onClick={() => handleTrigger(d.id)} disabled={triggering[d.id]}>
                          {triggering[d.id] ? '…' : '▶ Run'}
                        </button>
                        <button className="btn-secondary btn-sm" onClick={() => handlePause(d)}>
                          {d.paused ? 'Resume' : 'Pause'}
                        </button>
                        <Link to={`/dags/${d.id}/edit`}><button className="btn-secondary btn-sm">Edit</button></Link>
                        <button className="btn-danger btn-sm" onClick={() => handleDelete(d.id, d.name)}>Delete</button>
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
