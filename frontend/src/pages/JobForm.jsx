import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { api } from '../api'

const DEFAULT = {
  name: '',
  description: '',
  handler_config: '{\n  "type": "noop"\n}',
  input_spec: '',
  output_spec: '',
  input_validation_enabled: false,
  output_validation_enabled: false,
  validator_config: '',
  concurrency_enabled: false,
}

export default function JobForm() {
  const { id } = useParams()
  const isEdit = Boolean(id)
  const navigate = useNavigate()
  const [form, setForm] = useState(DEFAULT)
  const [error, setError] = useState(null)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (!isEdit) return
    api.getJob(id).then(j => {
      setForm({
        name: j.name,
        description: j.description || '',
        handler_config: JSON.stringify(j.handler_config, null, 2),
        input_spec: j.input_spec ? JSON.stringify(j.input_spec, null, 2) : '',
        output_spec: j.output_spec ? JSON.stringify(j.output_spec, null, 2) : '',
        input_validation_enabled: j.input_validation_enabled,
        output_validation_enabled: j.output_validation_enabled,
        validator_config: j.validator_config ? JSON.stringify(j.validator_config, null, 2) : '',
        concurrency_enabled: j.concurrency_enabled,
      })
    }).catch(e => setError(e.message))
  }, [id])

  const parseJson = (val, fieldName) => {
    if (!val.trim()) return null
    try { return JSON.parse(val) } catch {
      throw new Error(`${fieldName}: invalid JSON`)
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)
    setSaving(true)
    try {
      const payload = {
        name: form.name,
        description: form.description || null,
        handler_config: parseJson(form.handler_config, 'Handler Config'),
        input_spec: parseJson(form.input_spec, 'Input Spec'),
        output_spec: parseJson(form.output_spec, 'Output Spec'),
        input_validation_enabled: form.input_validation_enabled,
        output_validation_enabled: form.output_validation_enabled,
        validator_config: parseJson(form.validator_config, 'Validator Config'),
        concurrency_enabled: form.concurrency_enabled,
      }
      if (isEdit) await api.updateJob(id, payload)
      else await api.createJob(payload)
      navigate('/jobs')
    } catch (e) { setError(e.message) } finally { setSaving(false) }
  }

  const set = (k, v) => setForm(f => ({ ...f, [k]: v }))

  return (
    <div style={{ maxWidth: 720 }}>
      <div className="page-header">
        <h1>{isEdit ? 'Edit Job' : 'New Job'}</h1>
      </div>

      {error && <div className="error-msg">{error}</div>}

      <form onSubmit={handleSubmit}>
        <div className="card" style={{ marginBottom: 16 }}>
          <h3 style={{ marginBottom: 16, fontSize: 15 }}>Basic Info</h3>
          <div className="form-group">
            <label>Name *</label>
            <input required value={form.name} onChange={e => set('name', e.target.value)} placeholder="e.g. extract-orders" />
          </div>
          <div className="form-group">
            <label>Description</label>
            <input value={form.description} onChange={e => set('description', e.target.value)} placeholder="Optional description" />
          </div>
        </div>

        <div className="card" style={{ marginBottom: 16 }}>
          <h3 style={{ marginBottom: 4, fontSize: 15 }}>Handler Config</h3>
          <p style={{ color: 'var(--text-muted)', fontSize: 13, marginBottom: 12 }}>
            JSON object. <code style={{ color: 'var(--accent)' }}>{"{"}"type":"noop"{"}"}</code> or <code style={{ color: 'var(--accent)' }}>{"{"}"type":"script","command":"echo hello","timeout":60{"}"}</code>
          </p>
          <textarea
            required
            rows={5}
            value={form.handler_config}
            onChange={e => set('handler_config', e.target.value)}
            style={{ fontFamily: 'monospace', fontSize: 13 }}
          />
        </div>

        <div className="card" style={{ marginBottom: 16 }}>
          <h3 style={{ marginBottom: 12, fontSize: 15 }}>Validation</h3>
          <div className="checkbox-row">
            <input type="checkbox" id="iv" checked={form.input_validation_enabled} onChange={e => set('input_validation_enabled', e.target.checked)} />
            <label htmlFor="iv" style={{ margin: 0 }}>Enable input validation</label>
          </div>
          <div className="checkbox-row">
            <input type="checkbox" id="ov" checked={form.output_validation_enabled} onChange={e => set('output_validation_enabled', e.target.checked)} />
            <label htmlFor="ov" style={{ margin: 0 }}>Enable output validation</label>
          </div>
          {(form.input_validation_enabled || form.output_validation_enabled) && (
            <div className="form-group" style={{ marginTop: 12 }}>
              <label>Validator Config (JSON)</label>
              <textarea
                rows={4}
                value={form.validator_config}
                onChange={e => set('validator_config', e.target.value)}
                style={{ fontFamily: 'monospace', fontSize: 13 }}
                placeholder='{"type": "script", "command": "validate.sh"}'
              />
            </div>
          )}
        </div>

        <div className="card" style={{ marginBottom: 16 }}>
          <h3 style={{ marginBottom: 12, fontSize: 15 }}>Concurrency</h3>
          <div className="checkbox-row">
            <input type="checkbox" id="cc" checked={form.concurrency_enabled} onChange={e => set('concurrency_enabled', e.target.checked)} />
            <label htmlFor="cc" style={{ margin: 0 }}>Allow concurrent runs of this job</label>
          </div>
          <p style={{ color: 'var(--text-muted)', fontSize: 12, marginTop: 4 }}>
            When disabled, only one instance of this job runs at a time across all DAGs.
          </p>
        </div>

        <div style={{ display: 'flex', gap: 12 }}>
          <button type="submit" className="btn-primary" disabled={saving}>
            {saving ? 'Saving…' : isEdit ? 'Save Changes' : 'Create Job'}
          </button>
          <button type="button" className="btn-secondary" onClick={() => navigate('/jobs')}>Cancel</button>
        </div>
      </form>
    </div>
  )
}
