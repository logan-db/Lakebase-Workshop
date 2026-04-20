import { useState, useEffect } from 'react'
import { api } from './api'
import Dashboard from './pages/Dashboard'
import BranchManager from './pages/BranchManager'
import ComputePage from './pages/ComputePage'
import LoadTestPage from './pages/LoadTestPage'
import DataPlayground from './pages/DataPlayground'
import SyncStatus from './pages/SyncStatus'
import ApiTester from './pages/ApiTester'
import AgentMemory from './pages/AgentMemory'

const NAV_ITEMS = [
  { id: 'dashboard', label: 'Dashboard', icon: '\u25C8', section: 'overview' },
  { id: 'branches', label: 'Branches', icon: '\u2442', section: 'manage' },
  { id: 'compute', label: 'Autoscaling', icon: '\u26A1', section: 'manage' },
  { id: 'loadtest', label: 'Load Test', icon: '\uD83D\uDE80', section: 'manage' },
  { id: 'data', label: 'Data Ops', icon: '\uD83D\uDDC3', section: 'data' },
  { id: 'sync', label: 'Reverse ETL', icon: '\uD83D\uDD04', section: 'data' },
  { id: 'agent', label: 'Agent Memory', icon: '\uD83E\uDD16', section: 'data' },
  { id: 'api', label: 'API Tester', icon: '\uD83D\uDD0C', section: 'tools' },
]

const SECTIONS = [
  { key: 'overview', label: 'Overview' },
  { key: 'manage', label: 'Infrastructure' },
  { key: 'data', label: 'Data & AI' },
  { key: 'tools', label: 'Tools' },
]

export default function App() {
  const [activePage, setActivePage] = useState('dashboard')
  const [dbStatus, setDbStatus] = useState(null)
  const [config, setConfig] = useState(null)

  useEffect(() => {
    api.dbtest().then(setDbStatus).catch(() => setDbStatus({ db_connected: false }))
    api.config().then(setConfig).catch(() => {})
  }, [])

  const renderPage = () => {
    switch (activePage) {
      case 'dashboard': return <Dashboard onNavigate={setActivePage} />
      case 'branches': return <BranchManager />
      case 'compute': return <ComputePage />
      case 'loadtest': return <LoadTestPage />
      case 'data': return <DataPlayground />
      case 'sync': return <SyncStatus config={config} />
      case 'api': return <ApiTester />
      case 'agent': return <AgentMemory />
      default: return <Dashboard onNavigate={setActivePage} />
    }
  }

  return (
    <div className="app-layout">
      <aside className="sidebar">
        <div className="sidebar-brand">
          <h1>Lakebase Console</h1>
          <p>{config?.project_id || 'loading...'}</p>
        </div>
        <ul className="sidebar-nav">
          {SECTIONS.map((section) => {
            const items = NAV_ITEMS.filter((i) => i.section === section.key)
            if (items.length === 0) return null
            return (
              <li key={section.key}>
                <div className="sidebar-section-label">{section.label}</div>
                <ul style={{ listStyle: 'none' }}>
                  {items.map((item) => (
                    <li key={item.id}>
                      <a
                        href="#"
                        className={activePage === item.id ? 'active' : ''}
                        onClick={(e) => { e.preventDefault(); setActivePage(item.id) }}
                      >
                        <span className="nav-icon">{item.icon}</span>
                        <span>{item.label}</span>
                      </a>
                    </li>
                  ))}
                </ul>
              </li>
            )
          })}
        </ul>
        <div className="sidebar-status">
          <span className={`status-dot ${dbStatus?.db_connected ? 'connected' : 'disconnected'}`} />
          {dbStatus?.db_connected ? 'Connected' : 'Disconnected'}
        </div>
      </aside>
      <main className="main-content">
        {renderPage()}
      </main>
    </div>
  )
}
