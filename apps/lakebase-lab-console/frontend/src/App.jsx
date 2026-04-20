import { useState, useEffect } from 'react'
import { api } from './api'
import BranchManager from './pages/BranchManager'
import ComputePage from './pages/ComputePage'
import LoadTestPage from './pages/LoadTestPage'
import DataPlayground from './pages/DataPlayground'
import SyncStatus from './pages/SyncStatus'
import ApiTester from './pages/ApiTester'
import AgentMemory from './pages/AgentMemory'

const NAV_ITEMS = [
  { id: 'branches', label: 'Branch Manager', icon: '⑂' },
  { id: 'compute', label: 'Autoscaling', icon: '⚡' },
  { id: 'loadtest', label: 'Load Test', icon: '📊' },
  { id: 'data', label: 'Data Playground', icon: '🗄' },
  { id: 'sync', label: 'Reverse ETL', icon: '🔄' },
  { id: 'api', label: 'API Tester', icon: '🔌' },
  { id: 'agent', label: 'Agent Memory', icon: '🤖' },
]

export default function App() {
  const [activePage, setActivePage] = useState('branches')
  const [dbStatus, setDbStatus] = useState(null)
  const [config, setConfig] = useState(null)

  useEffect(() => {
    api.dbtest().then(setDbStatus).catch(() => setDbStatus({ db_connected: false }))
    api.config().then(setConfig).catch(() => {})
  }, [])

  const renderPage = () => {
    switch (activePage) {
      case 'branches': return <BranchManager />
      case 'compute': return <ComputePage />
      case 'loadtest': return <LoadTestPage />
      case 'data': return <DataPlayground />
      case 'sync': return <SyncStatus config={config} />
      case 'api': return <ApiTester />
      case 'agent': return <AgentMemory />
      default: return <BranchManager />
    }
  }

  return (
    <div className="app-layout">
      <aside className="sidebar">
        <div className="sidebar-brand">
          <h1>Lakebase Lab Console</h1>
          <p>{config?.project_id || 'Loading...'}</p>
        </div>
        <ul className="sidebar-nav">
          {NAV_ITEMS.map((item) => (
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
