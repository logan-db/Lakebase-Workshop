import { useState, useEffect } from 'react'
import { api } from '../api'
import { Database, RefreshCw, Table, Server, Activity, AlertCircle, Check, Clock, ChevronRight, Layers } from '../icons'

export default function OnlineTablesPage() {
  const [tab, setTab] = useState('synced')
  const [onlineStores, setOnlineStores] = useState([])
  const [syncedTables, setSyncedTables] = useState([])
  const [featureSpecs, setFeatureSpecs] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const loadAll = async () => {
    setLoading(true)
    setError(null)
    try {
      const [stores, synced, features] = await Promise.allSettled([
        api.listOnlineStores(),
        api.listSyncedTables(),
        api.listFeatureSpecs(),
      ])
      if (stores.status === 'fulfilled') setOnlineStores(stores.value)
      if (synced.status === 'fulfilled') setSyncedTables(synced.value)
      if (features.status === 'fulfilled') setFeatureSpecs(features.value)
    } catch (e) {
      setError(e.message)
    }
    setLoading(false)
  }

  useEffect(() => { loadAll() }, [])

  const stateColor = (state) => {
    if (!state) return 'badge-info'
    const s = state.toLowerCase()
    if (s.includes('active') || s.includes('online') || s.includes('ready')) return 'badge-success'
    if (s.includes('provisioning') || s.includes('creating') || s.includes('updating')) return 'badge-warning'
    if (s.includes('failed') || s.includes('error')) return 'badge-danger'
    return 'badge-info'
  }

  const totalItems = onlineStores.length + syncedTables.length + featureSpecs.length

  return (
    <div>
      <div className="page-header">
        <div className="page-header-row">
          <div>
            <h2>Online Tables & Synced Data</h2>
            <p>
              View Lakebase-backed online stores for feature serving, synced tables from
              Unity Catalog (reverse ETL), and online table specs for real-time feature access.
            </p>
          </div>
          <button className="btn btn-secondary btn-sm" onClick={loadAll} disabled={loading}>
            <RefreshCw size={14} /> {loading ? 'Refreshing...' : 'Refresh'}
          </button>
        </div>
      </div>

      {error && (
        <div className="card" style={{ borderColor: 'rgba(239, 68, 68, 0.3)', marginBottom: 16 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <AlertCircle size={18} style={{ color: 'var(--danger)' }} />
            <p style={{ color: 'var(--danger)' }}>{error}</p>
          </div>
        </div>
      )}

      <div className="metrics-row" style={{ gridTemplateColumns: 'repeat(3, 1fr)' }}>
        <div className="metric-card">
          <div className="metric-icon"><Server size={18} /></div>
          <div className="metric-value">{onlineStores.length}</div>
          <div className="metric-label">Online Stores</div>
        </div>
        <div className="metric-card">
          <div className="metric-icon"><RefreshCw size={18} /></div>
          <div className="metric-value">{syncedTables.length}</div>
          <div className="metric-label">Synced Tables</div>
        </div>
        <div className="metric-card">
          <div className="metric-icon"><Table size={18} /></div>
          <div className="metric-value">{featureSpecs.length}</div>
          <div className="metric-label">Feature Specs</div>
        </div>
      </div>

      <div className="tab-group">
        <button className={`tab-btn ${tab === 'synced' ? 'active' : ''}`} onClick={() => setTab('synced')}>
          Synced Tables ({syncedTables.length})
        </button>
        <button className={`tab-btn ${tab === 'stores' ? 'active' : ''}`} onClick={() => setTab('stores')}>
          Online Stores ({onlineStores.length})
        </button>
        <button className={`tab-btn ${tab === 'features' ? 'active' : ''}`} onClick={() => setTab('features')}>
          Feature Specs ({featureSpecs.length})
        </button>
        <button className={`tab-btn ${tab === 'guide' ? 'active' : ''}`} onClick={() => setTab('guide')}>
          How It Works
        </button>
      </div>

      {/* ── Synced Tables ── */}
      {tab === 'synced' && (
        <div className="card">
          <div className="card-header">
            <h3><RefreshCw size={16} /> Synced Database Tables</h3>
          </div>
          {loading ? (
            <div className="empty-state" style={{ padding: 20 }}><p>Loading...</p></div>
          ) : syncedTables.length === 0 ? (
            <div className="empty-state">
              <div className="empty-icon"><RefreshCw size={36} /></div>
              <p>No synced tables found. Create one using the Reverse ETL lab notebook.</p>
              <div className="code-block" style={{ marginTop: 16, textAlign: 'left', maxWidth: 600, margin: '16px auto' }}>{`from databricks.sdk import WorkspaceClient
from databricks.sdk.service.database import (
    SyncedDatabaseTable, SyncedTableSpec,
    NewPipelineSpec, SyncedTableSchedulingPolicy,
)

w = WorkspaceClient()
w.database.create_synced_database_table(
    SyncedDatabaseTable(
        name="<project>.production.products_synced",
        spec=SyncedTableSpec(
            source_table_full_name="<catalog>.<schema>.products",
            primary_key_columns=["product_id"],
            scheduling_policy=SyncedTableSchedulingPolicy.TRIGGERED,
        ),
    )
)`}</div>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              {syncedTables.map((t, i) => (
                <div key={i} style={{ padding: 18, background: 'var(--bg-secondary)', border: '1px solid var(--border)', borderRadius: 'var(--radius)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
                    <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 600, fontSize: 14 }}>{t.table_id || t.name}</span>
                    <div style={{ display: 'flex', gap: 6 }}>
                      {t.state && <span className={`badge ${stateColor(t.state)}`}>{t.state}</span>}
                      <span className="badge badge-info">{t.branch_id}</span>
                    </div>
                  </div>
                  {t.source_table && (
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 12, color: 'var(--text-secondary)', marginBottom: 6 }}>
                      <Database size={12} /> Source: <code style={{ color: 'var(--accent)' }}>{t.source_table}</code>
                    </div>
                  )}
                  {t.primary_key_columns && t.primary_key_columns.length > 0 && (
                    <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                      PK: {t.primary_key_columns.map(k => <span key={k} className="badge badge-teal" style={{ marginRight: 4, fontSize: 10 }}>{k}</span>)}
                    </div>
                  )}
                  {t.scheduling_policy && (
                    <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 4 }}>
                      Schedule: <span className="badge badge-purple" style={{ fontSize: 10 }}>{t.scheduling_policy}</span>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ── Online Stores ── */}
      {tab === 'stores' && (
        <div className="card">
          <div className="card-header">
            <h3><Server size={16} /> Lakebase Online Stores</h3>
          </div>
          {loading ? (
            <div className="empty-state" style={{ padding: 20 }}><p>Loading...</p></div>
          ) : onlineStores.length === 0 ? (
            <div className="empty-state">
              <div className="empty-icon"><Server size={36} /></div>
              <p>No online stores found. Create one via the Online Feature Store lab notebook.</p>
              <div className="code-block" style={{ marginTop: 16, textAlign: 'left', maxWidth: 600, margin: '16px auto' }}>{`w = WorkspaceClient()
w.postgres.create_online_store(
    parent="projects/<project_id>",
    online_store=OnlineStore(
        spec=OnlineStoreSpec(
            source_table_full_name="<catalog>.<schema>.features",
            primary_key_columns=["id"],
        )
    ),
    online_store_id="my-feature-store"
)`}</div>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              {onlineStores.map((s, i) => (
                <div key={i} style={{ padding: 18, background: 'var(--bg-secondary)', border: '1px solid var(--border)', borderRadius: 'var(--radius)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
                    <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 600, fontSize: 14 }}>{s.store_id || s.name}</span>
                    {s.state && <span className={`badge ${stateColor(s.state)}`}>{s.state}</span>}
                  </div>
                  {s.source_table && (
                    <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
                      <Database size={12} style={{ verticalAlign: -2 }} /> Source: <code style={{ color: 'var(--accent)' }}>{s.source_table}</code>
                    </div>
                  )}
                  {s.primary_key_columns && s.primary_key_columns.length > 0 && (
                    <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 4 }}>
                      PK: {s.primary_key_columns.map(k => <span key={k} className="badge badge-teal" style={{ marginRight: 4, fontSize: 10 }}>{k}</span>)}
                    </div>
                  )}
                  {s.detailed_state && (
                    <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4 }}>{s.detailed_state}</div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ── Feature Specs ── */}
      {tab === 'features' && (
        <div className="card">
          <div className="card-header">
            <h3><Table size={16} /> Unity Catalog Online Table Specs</h3>
          </div>
          {loading ? (
            <div className="empty-state" style={{ padding: 20 }}><p>Loading...</p></div>
          ) : featureSpecs.length === 0 ? (
            <div className="empty-state">
              <div className="empty-icon"><Table size={36} /></div>
              <p>No online table feature specs found. These are created via the Feature Engineering client or UC API.</p>
            </div>
          ) : (
            <table className="data-table">
              <thead>
                <tr><th>Name</th><th>Source Table</th><th>Primary Key</th><th>State</th><th>Mode</th></tr>
              </thead>
              <tbody>
                {featureSpecs.map((f, i) => (
                  <tr key={i}>
                    <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 600 }}>{f.name}</td>
                    <td style={{ fontFamily: 'var(--font-mono)', fontSize: 12 }}>{f.source_table || '--'}</td>
                    <td>{(f.primary_key_columns || []).map(k => <span key={k} className="badge badge-teal" style={{ marginRight: 4, fontSize: 10 }}>{k}</span>)}</td>
                    <td><span className={`badge ${stateColor(f.state)}`}>{f.state || '--'}</span></td>
                    <td style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
                      {f.run_continuously ? 'Continuous' : f.run_triggered ? 'Triggered' : 'Snapshot'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      {/* ── How It Works Guide ── */}
      {tab === 'guide' && (
        <>
          <div className="card">
            <div className="card-header">
              <h3><Layers size={16} /> Synced Tables (Reverse ETL)</h3>
            </div>
            <div className="flow-diagram flow-5">
              <div className="flow-box">
                <div style={{ marginBottom: 8 }}><Database size={28} style={{ color: 'var(--blue)' }} /></div>
                <div className="flow-box-title">Delta Table</div>
                <div className="flow-box-subtitle">Unity Catalog</div>
              </div>
              <div className="flow-arrow"><ChevronRight size={32} /></div>
              <div className="flow-box">
                <div style={{ marginBottom: 8 }}><Activity size={28} style={{ color: 'var(--teal)' }} /></div>
                <div className="flow-box-title">Sync Pipeline</div>
                <div className="flow-box-subtitle">Lakeflow</div>
              </div>
              <div className="flow-arrow"><ChevronRight size={32} /></div>
              <div className="flow-box">
                <div style={{ marginBottom: 8 }}><Database size={28} style={{ color: 'var(--accent)' }} /></div>
                <div className="flow-box-title">PostgreSQL Table</div>
                <div className="flow-box-subtitle">Lakebase</div>
              </div>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10, marginTop: 12 }}>
              <div className="info-box info">
                <span style={{ fontWeight: 600 }}>Snapshot:</span>
                <span>One-time full table copy. Good for initial data loading.</span>
              </div>
              <div className="info-box warning">
                <span style={{ fontWeight: 600 }}>Triggered:</span>
                <span>On-demand incremental updates via CDF. Requires <code>delta.enableChangeDataFeed = true</code>.</span>
              </div>
              <div className="info-box info">
                <span style={{ fontWeight: 600 }}>Continuous:</span>
                <span>Real-time streaming sync with second-level latency.</span>
              </div>
            </div>
          </div>

          <div className="card">
            <div className="card-header">
              <h3><Server size={16} /> Online Feature Stores</h3>
            </div>
            <div className="flow-diagram flow-5">
              <div className="flow-box">
                <div style={{ marginBottom: 8 }}><Table size={28} style={{ color: 'var(--blue)' }} /></div>
                <div className="flow-box-title">Feature Table</div>
                <div className="flow-box-subtitle">Delta + CDF</div>
              </div>
              <div className="flow-arrow"><ChevronRight size={32} /></div>
              <div className="flow-box">
                <div style={{ marginBottom: 8 }}><Database size={28} style={{ color: 'var(--accent)' }} /></div>
                <div className="flow-box-title">Online Store</div>
                <div className="flow-box-subtitle">Lakebase-backed</div>
              </div>
              <div className="flow-arrow"><ChevronRight size={32} /></div>
              <div className="flow-box">
                <div style={{ marginBottom: 8 }}><Activity size={28} style={{ color: 'var(--success)' }} /></div>
                <div className="flow-box-title">Feature Serving</div>
                <div className="flow-box-subtitle">Low-latency lookups</div>
              </div>
            </div>
            <p style={{ color: 'var(--text-secondary)', fontSize: 13, lineHeight: 1.7, marginTop: 12 }}>
              Online stores provide sub-millisecond feature lookups for ML models at inference time.
              Data is synced from Delta tables via the <code>publish_table</code> API. Lakebase provides
              the PostgreSQL-compatible serving layer with autoscaling compute.
            </p>
          </div>
        </>
      )}
    </div>
  )
}
