const BASE = '/api'

async function request(method, path, body) {
  const opts = {
    method,
    headers: { 'Content-Type': 'application/json' },
  }
  if (body !== undefined) opts.body = JSON.stringify(body)
  const res = await fetch(BASE + path, opts)
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || res.statusText)
  }
  if (res.status === 204) return null
  return res.json()
}

export const api = {
  // Jobs
  listJobs: () => request('GET', '/jobs'),
  getJob: (id) => request('GET', `/jobs/${id}`),
  createJob: (data) => request('POST', '/jobs', data),
  updateJob: (id, data) => request('PUT', `/jobs/${id}`, data),
  deleteJob: (id) => request('DELETE', `/jobs/${id}`),

  // DAGs
  listDags: () => request('GET', '/dags'),
  getDag: (id) => request('GET', `/dags/${id}`),
  createDag: (data) => request('POST', '/dags', data),
  updateDag: (id, data) => request('PUT', `/dags/${id}`, data),
  deleteDag: (id) => request('DELETE', `/dags/${id}`),
  validateDag: (id) => request('POST', `/dags/${id}/validate`),
  triggerRun: (dagId, body = {}) => request('POST', `/dags/${dagId}/runs`, body),
  listDagRuns: (dagId) => request('GET', `/dags/${dagId}/runs`),

  // Runs
  listRuns: () => request('GET', '/runs'),
  getRun: (id) => request('GET', `/runs/${id}`),
  cancelRun: (id) => request('POST', `/runs/${id}/cancel`),
  getJobStatus: (runId, jobId) => request('GET', `/runs/${runId}/jobs/${jobId}/status`),

  // Settings
  getRetention: () => request('GET', '/settings/retention'),
  updateRetention: (days) => request('PUT', '/settings/retention', { retention_days: days }),
}
