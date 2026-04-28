import { useState, useEffect } from 'react'
import { api } from './api'
import {
  LayoutDashboard, TrendingUp, GitBranch, Cpu,
  Database, RefreshCw, Bot, Terminal, Layers, Sun, Moon, ExternalLink,
  Activity, Table
} from './icons'
import Dashboard from './pages/Dashboard'
import BranchManager from './pages/BranchManager'
import ComputePage from './pages/ComputePage'
import AutoscaleDemo from './pages/AutoscaleDemo'
import LoadTestPage from './pages/LoadTestPage'
import DataPlayground from './pages/DataPlayground'
import SyncStatus from './pages/SyncStatus'
import ApiTester from './pages/ApiTester'
import AgentMemory from './pages/AgentMemory'
import ObservabilityPage from './pages/ObservabilityPage'
import FeatureStorePage from './pages/FeatureStorePage'

const NAV_ITEMS = [
  { id: 'dashboard', label: 'Dashboard', Icon: LayoutDashboard, section: 'overview' },
  { id: 'autoscale', label: 'Autoscale Demo', Icon: TrendingUp, section: 'overview' },
  { id: 'data', label: 'Data Ops', Icon: Database, section: 'labs' },
  { id: 'observability', label: 'Observability', Icon: Activity, section: 'labs' },
  { id: 'sync', label: 'Reverse ETL', Icon: RefreshCw, section: 'labs' },
  { id: 'feature-store', label: 'Feature Store', Icon: Layers, section: 'labs' },
  { id: 'agent', label: 'Agent Memory', Icon: Bot, section: 'labs' },
  { id: 'branches', label: 'Branches', Icon: GitBranch, section: 'manage' },
  { id: 'compute', label: 'Compute', Icon: Cpu, section: 'manage' },
  { id: 'api', label: 'API Tester', Icon: Terminal, section: 'tools' },
]

const SECTIONS = [
  { key: 'overview', label: 'Overview' },
  { key: 'labs', label: 'Labs' },
  { key: 'manage', label: 'Infrastructure' },
  { key: 'tools', label: 'Tools' },
]

function getInitialTheme() {
  const stored = localStorage.getItem('lakebase-theme')
  if (stored === 'light' || stored === 'dark') return stored
  return window.matchMedia?.('(prefers-color-scheme: light)').matches ? 'light' : 'dark'
}

export default function App() {
  const [activePage, setActivePage] = useState('dashboard')
  const [dbStatus, setDbStatus] = useState(null)
  const [config, setConfig] = useState(null)
  const [theme, setTheme] = useState(getInitialTheme)

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
    localStorage.setItem('lakebase-theme', theme)
  }, [theme])

  const toggleTheme = () => setTheme((t) => (t === 'dark' ? 'light' : 'dark'))

  useEffect(() => {
    api.dbtest().then(setDbStatus).catch(() => setDbStatus({ db_connected: false }))
    api.config().then(setConfig).catch(() => {})
  }, [])

  const renderPage = () => {
    switch (activePage) {
      case 'dashboard': return <Dashboard onNavigate={setActivePage} />
      case 'autoscale': return <AutoscaleDemo />
      case 'branches': return <BranchManager />
      case 'compute': return <ComputePage />
      case 'loadtest': return <LoadTestPage />
      case 'data': return <DataPlayground />
      case 'sync': return <SyncStatus config={config} />
      case 'api': return <ApiTester />
      case 'agent': return <AgentMemory />
      case 'observability': return <ObservabilityPage />
      case 'feature-store': return <FeatureStorePage />
      default: return <Dashboard onNavigate={setActivePage} />
    }
  }

  return (
    <div className="app-layout">
      <aside className="sidebar">
        <div className="sidebar-brand">
          <div className="sidebar-brand-row">
            <div className="sidebar-logo">
              <Layers size={18} />
            </div>
            <h1>Lakebase Lab</h1>
          </div>
          {config?.project_id && <p>{config.project_id}</p>}
        </div>
        <ul className="sidebar-nav">
          {SECTIONS.map((section) => {
            const items = NAV_ITEMS.filter((i) => i.section === section.key)
            if (items.length === 0) return null
            return (
              <li key={section.key}>
                <div className="sidebar-section-label">{section.label}</div>
                <ul>
                  {items.map((item) => (
                    <li key={item.id}>
                      <a
                        href="#"
                        className={activePage === item.id ? 'active' : ''}
                        onClick={(e) => { e.preventDefault(); setActivePage(item.id) }}
                      >
                        <span className="nav-icon"><item.Icon size={16} /></span>
                        <span>{item.label}</span>
                      </a>
                    </li>
                  ))}
                </ul>
              </li>
            )
          })}
        </ul>
        <div className="sidebar-footer">
          <div className="sidebar-status">
            <span className={`status-dot ${dbStatus?.db_connected ? 'connected' : 'disconnected'}`} />
            <span style={{ flex: 1 }}>{dbStatus?.db_connected ? 'Connected' : 'Disconnected'}</span>
            <button className="theme-toggle" onClick={toggleTheme} title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}>
              {theme === 'dark' ? <Sun size={15} /> : <Moon size={15} />}
            </button>
          </div>
          {dbStatus?.db_connected && config?.workspace_host && config?.project_id && (
            <a
              className="lakebase-link"
              href={`${config.workspace_host}/lakebase/projects/${config.project_id}${config.branch_id ? `?branchId=${config.branch_id}` : ''}`}
              target="_blank"
              rel="noopener noreferrer"
            >
              <Database size={14} />
              <span>Open in Lakebase</span>
              <ExternalLink size={12} />
            </a>
          )}
        </div>
      </aside>
      <main className="main-content">
        {renderPage()}
      </main>
    </div>
  )
}
