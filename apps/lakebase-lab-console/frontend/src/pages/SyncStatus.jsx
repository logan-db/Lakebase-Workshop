import { useState, useEffect } from 'react'
import { api } from '../api'

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
        <h3 style={{ marginBottom: 16 }}>How Reverse ETL Works</h3>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr auto 1fr', gap: 16, alignItems: 'center', marginBottom: 20 }}>
          <div style={{ padding: 16, background: 'var(--bg-primary)', borderRadius: 'var(--radius)', textAlign: 'center' }}>
            <div style={{ fontSize: 24, marginBottom: 8 }}>Delta Table</div>
            <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>Unity Catalog</div>
            <div style={{ fontSize: 11, color: 'var(--text-secondary)', marginTop: 4 }}>analytics.gold.user_profiles</div>
          </div>
          <div style={{ fontSize: 32, color: 'var(--accent)' }}>→</div>
          <div style={{ padding: 16, background: 'var(--bg-primary)', borderRadius: 'var(--radius)', textAlign: 'center' }}>
            <div style={{ fontSize: 24, marginBottom: 8 }}>PostgreSQL Table</div>
            <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>Lakebase</div>
            <div style={{ fontSize: 11, color: 'var(--text-secondary)', marginTop: 4 }}>demo.user_profiles_synced</div>
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
              <td>Minutes</td>
              <td>Initial setup, historical data</td>
            </tr>
            <tr>
              <td><span className="badge badge-warning">Triggered</span></td>
              <td>Scheduled updates on demand</td>
              <td>Minutes</td>
              <td>Hourly/daily dashboards</td>
            </tr>
            <tr>
              <td><span className="badge badge-success">Continuous</span></td>
              <td>Real-time streaming</td>
              <td>Seconds</td>
              <td>Live applications</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div className="card">
        <h3 style={{ marginBottom: 16 }}>Create a Synced Table</h3>
        <p style={{ color: 'var(--text-secondary)', fontSize: 13, marginBottom: 16 }}>
          Synced tables are created via the Databricks SDK or UI. Use the optional lab notebook
          at <code>labs/reverse-etl/</code> to set up a synced table for this project.
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
        <h3 style={{ marginBottom: 16 }}>Important Notes</h3>
        <ul style={{ fontSize: 13, color: 'var(--text-secondary)', paddingLeft: 20 }}>
          <li style={{ marginBottom: 8 }}>
            <strong>CDF Required:</strong> Enable Change Data Feed on the source table for
            Triggered/Continuous modes: <code>ALTER TABLE ... SET TBLPROPERTIES (delta.enableChangeDataFeed = true)</code>
          </li>
          <li style={{ marginBottom: 8 }}>
            <strong>SP Permissions:</strong> After sync completes, you must re-grant the App's
            Service Principal access to the new table. Synced tables are created by the sync pipeline,
            not your user, so <code>ALTER DEFAULT PRIVILEGES</code> does not cover them.
          </li>
          <li style={{ marginBottom: 8 }}>
            <strong>Connection Limits:</strong> Each synced table uses up to 16 connections.
            Plan your compute sizing accordingly.
          </li>
          <li>
            <strong>Size Limits:</strong> 2 TB total across all synced tables per project.
          </li>
        </ul>
      </div>

      <div className="card">
        <h3 style={{ marginBottom: 12 }}>Quick Links</h3>
        <div style={{ display: 'flex', gap: 12 }}>
          <a
            href={config?.project_id ? `#` : '#'}
            className="btn btn-secondary"
            target="_blank"
            rel="noopener"
          >
            Open Lakebase UI
          </a>
          <a href="#" className="btn btn-secondary" target="_blank" rel="noopener">
            Open Catalog Explorer
          </a>
          <button className="btn btn-secondary" onClick={checkSync} disabled={checking}>
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
