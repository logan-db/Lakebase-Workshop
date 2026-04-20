# Reverse ETL

Sync Delta Lake tables from the Lakehouse into Lakebase PostgreSQL for low-latency serving.

## Labs

| Order | Lab | What You'll Learn |
|-------|-----|-------------------|
| 1 | `Reverse_ETL` | Create a CDF-enabled Delta table, set up a synced table, monitor sync status |
| 2 | `create_synced_table` | Minimal standalone reference for synced table setup |

## Prerequisites

- Complete **`00_Setup_Lakebase_Project`** (foundation)
- A Unity Catalog schema with write access (the lab creates one)

## Key Concepts

- **Synced tables** — Automatic one-way sync from Delta Lake → Lakebase PostgreSQL
- **Change Data Feed (CDF)** — Delta table feature that tracks row-level changes for incremental sync
- **Service Principal grants** — Required for the sync pipeline to write into Lakebase

## Notes

See `docs/PERMISSIONS.md` for the Service Principal grants needed for synced tables.
