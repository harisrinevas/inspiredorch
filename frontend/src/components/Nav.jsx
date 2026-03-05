import { NavLink } from 'react-router-dom'

const links = [
  { to: '/', label: 'Dashboard' },
  { to: '/jobs', label: 'Jobs' },
  { to: '/dags', label: 'DAGs' },
  { to: '/runs', label: 'Runs' },
  { to: '/settings', label: 'Settings' },
]

export default function Nav() {
  return (
    <nav style={{
      width: 220,
      minHeight: '100vh',
      background: 'var(--surface)',
      borderRight: '1px solid var(--border)',
      padding: '24px 0',
      flexShrink: 0,
    }}>
      <div style={{ padding: '0 20px 24px', borderBottom: '1px solid var(--border)' }}>
        <div style={{ fontSize: 18, fontWeight: 700, color: 'var(--text)' }}>⚙ Orchestrator</div>
        <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 4 }}>Pipeline Manager</div>
      </div>
      <ul style={{ listStyle: 'none', padding: '12px 0' }}>
        {links.map(({ to, label }) => (
          <li key={to}>
            <NavLink
              to={to}
              end={to === '/'}
              style={({ isActive }) => ({
                display: 'block',
                padding: '10px 20px',
                color: isActive ? 'var(--accent-hover)' : 'var(--text-muted)',
                background: isActive ? 'rgba(99,102,241,0.1)' : 'transparent',
                borderLeft: isActive ? '3px solid var(--accent)' : '3px solid transparent',
                fontWeight: isActive ? 600 : 400,
                fontSize: 14,
                transition: 'all 0.15s',
              })}
            >
              {label}
            </NavLink>
          </li>
        ))}
      </ul>
    </nav>
  )
}
