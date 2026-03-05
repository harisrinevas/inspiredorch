import { Routes, Route } from 'react-router-dom'
import Nav from './components/Nav'
import Dashboard from './pages/Dashboard'
import Jobs from './pages/Jobs'
import JobForm from './pages/JobForm'
import DAGs from './pages/DAGs'
import DAGForm from './pages/DAGForm'
import Runs from './pages/Runs'
import RunDetail from './pages/RunDetail'
import Settings from './pages/Settings'

export default function App() {
  return (
    <div style={{ display: 'flex', minHeight: '100vh' }}>
      <Nav />
      <main style={{ flex: 1, padding: 32, maxWidth: 1200 }}>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/jobs" element={<Jobs />} />
          <Route path="/jobs/new" element={<JobForm />} />
          <Route path="/jobs/:id/edit" element={<JobForm />} />
          <Route path="/dags" element={<DAGs />} />
          <Route path="/dags/new" element={<DAGForm />} />
          <Route path="/dags/:id/edit" element={<DAGForm />} />
          <Route path="/runs" element={<Runs />} />
          <Route path="/runs/:id" element={<RunDetail />} />
          <Route path="/settings" element={<Settings />} />
        </Routes>
      </main>
    </div>
  )
}
