import { useEffect, useState } from 'react'
import { api } from '../api'

export default function Settings() {
  const [retention, setRetention] = useState('')
  const [saved, setSaved] = useState(false)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.getRetention()
      .then(r => setRetention(r.value))
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  const handleSave = async (e) => {
    e.preventDefault()
    setError(null)
    setSaved(false)
    try {
      await api.updateRetention(parseInt(retention))
      setSaved(true)
      setTimeout(() => setSaved(false), 3000)
    } catch (e) { setError(e.message) }
  }

  return (
    <div style={{ maxWidth: 560 }}>
      <div className="page-header">
        <h1>Settings</h1>
      </div>

      {error && <div className="error-msg">{error}</div>}

      {loading ? <p style={{ color: 'var(--text-muted)' }}>Loading…</p> : (
        <div className="card">
          <h2 style={{ fontSize: 16, fontWeight: 600, marginBottom: 6 }}>Data Retention</h2>
          <p style={{ color: 'var(--text-muted)', fontSize: 13, marginBottom: 20 }}>
            Run records older than this many days are deleted. Changes take effect immediately on the next retention sweep.
            Individual DAGs can override this per-DAG in the DAG editor.
          </p>
          <form onSubmit={handleSave}>
            <div className="form-group">
              <label>Retention (days)</label>
              <input
                type="number"
                min="1"
                required
                value={retention}
                onChange={e => setRetention(e.target.value)}
                style={{ maxWidth: 200 }}
              />
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <button type="submit" className="btn-primary">Save</button>
              {saved && <span style={{ color: 'var(--success)', fontSize: 14 }}>✓ Saved</span>}
            </div>
          </form>
        </div>
      )}
    </div>
  )
}
