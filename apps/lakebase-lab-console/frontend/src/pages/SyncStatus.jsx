import { useState } from 'react'
import { api } from '../api'
import { RefreshCw, Database, ExternalLink, ChevronRight, Check, Clock, Activity } from '../icons'

export default function SyncStatus({ config }) {
  const [syncedRows, setSyncedRows] = useState(null)
  const [checking, setChecking] = useState(false)

  const checkSync = async () => {
    setChecking(true)
    try {
      const res = await api.raw('GET', '/api/dbtest')
      setSyncedRows(res)
    } catch {}
    setChecking(false)
  }

  return (
    <div>
      <div className="page-header">
        <h2>Reverse ETL / Synced Tables</h2>
        <p>
          Sync data from Unity Catalog Delta tables into Lakebase as PostgreSQL tables.
          This enables OLTP access patterns on data processed in the Lakehouse.
        </p>
      </div>

      <div className="card">
        <div className="card-header">
          <h3><RefreshCw size={16} /> How Reverse ETL Works</h3>
        </div>

        <div className="flow-diagram">
          <div className="flow-box">
            <div style={{ marginBottom: 8 }}><Database size={28} style={{ color: 'var(--blue)' }} /></div>
            <div className="flow-box-title">Delta Table</div>
            <div className="flow-box-subtitle">Unity Catalog</div>
            <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4, fontFamily: 'var(--font-mono)' }}>analytics.gold.user_profiles</div>
          </div>
          <div className="flow-arrow">
            <ChevronRight size={32} />
          </div>
          <div className="flow-box">
            <div style={{ marginBottom: 8 }}><Database size={28} style={{ color: 'var(--accent)' }} /></div>
            <div className="flow-box-title">PostgreSQL Table</div>
            <div className="flow-box-subtitle">Lakebase</div>
            <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4, fontFamily: 'var(--font-mono)' }}>demo.user_profiles_synced</div>
          </div>
        </div>

        <table className="data-table">
          <thead>
            <tr><th>Sync Mode</th><th>Description</th><th>Latency</th><th>Best For</th></tr>
          </thead>
          <tbody>
            <tr>
              <td><span className="badge badge-info">Snapshot</span></td>
              <td>One-time full copy</td>
              <td><span style={{ display: 'flex', alignItems: 'center', gap: 4 }}><Clock size={12} /> Minutes</span></td>
              <td>Initial setup, historical data</td>
            </tr>
            <tr>
              <td><span className="badge badge-warning">Triggered</span></td>
              <td>Scheduled updates on demand</td>
              <td><span style={{ display: 'flex', alignItems: 'center', gap: 4 }}><Clock size={12} /> Minutes</span></td>
              <td>Hourly/daily dashboards</td>
            </tr>
            <tr>
              <td><span className="badge badge-success">Continuous</span></td>
              <td>Real-time streaming</td>
              <td><span style={{ display: 'flex', alignItems: 'center', gap: 4 }}><Activity size={12} /> Seconds</span></td>
              <td>Live applications</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div className="card">
        <div className="card-header">
          <h3>Create a Synced Table</h3>
        </div>
        <p style={{ color: 'var(--text-secondary)', fontSize: 13, marginBottom: 16, lineHeight: 1.6 }}>
          Synced tables are created via the Databricks SDK or UI. Use the optional lab notebook
          at <code style={{ color: 'var(--accent)' }}>labs/reverse-etl/</code> to set up a synced table for this project.
        </p>
        <div className="code-block">{`from databricks.sdk import WorkspaceClient
from databricks.sdk.service.database import (
    SyncedDatabaseTable, SyncedTableSpec,
    NewPipelineSpec, SyncedTableSchedulingPolicy,
)

w = WorkspaceClient()
w.database.create_synced_database_table(
    SyncedDatabaseTable(
        name="<lakebase_catalog>.<schema>.products_synced",
        spec=SyncedTableSpec(
            source_table_full_name="<catalog>.<schema>.products",
            primary_key_columns=["product_id"],
            scheduling_policy=SyncedTableSchedulingPolicy.TRIGGERED,
            new_pipeline_spec=NewPipelineSpec(
                storage_catalog="<lakebase_catalog>",
                storage_schema="staging"
            )
        ),
    )
)`}</div>
      </div>

      <div className="card">
        <div className="card-header">
          <h3>Important Notes</h3>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          <div className="info-box warning">
            <span style={{ fontWeight: 600 }}>CDF Required:</span>
            <span>Enable Change Data Feed on the source table for Triggered/Continuous modes: <code>ALTER TABLE ... SET TBLPROPERTIES (delta.enableChangeDataFeed = true)</code></span>
          </div>
          <div className="info-box info">
            <span style={{ fontWeight: 600 }}>SP Permissions:</span>
            <span>After sync completes, re-grant the App's Service Principal access to the new table. Synced tables are created by the sync pipeline.</span>
          </div>
          <div className="info-box info">
            <span style={{ fontWeight: 600 }}>Connection Limits:</span>
            <span>Each synced table uses up to 16 connections. Plan your compute sizing accordingly.</span>
          </div>
          <div className="info-box danger">
            <span style={{ fontWeight: 600 }}>Size Limits:</span>
            <span>8 TB total across all synced tables per project.</span>
          </div>
        </div>
      </div>

      <div className="card">
        <div className="card-header">
          <h3>Quick Links</h3>
        </div>
        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
          <a
            href={config?.project_id ? `#` : '#'}
            className="btn btn-secondary"
            target="_blank"
            rel="noopener"
          >
            <ExternalLink size={14} /> Open Lakebase UI
          </a>
          <a href="#" className="btn btn-secondary" target="_blank" rel="noopener">
            <ExternalLink size={14} /> Open Catalog Explorer
          </a>
          <button className="btn btn-secondary" onClick={checkSync} disabled={checking}>
            <Activity size={14} />
            {checking ? 'Checking...' : 'Test DB Connection'}
          </button>
        </div>
        {syncedRows && (
          <div className="code-block" style={{ marginTop: 12 }}>
            {JSON.stringify(syncedRows, null, 2)}
          </div>
        )}
      </div>
    </div>
  )
}
