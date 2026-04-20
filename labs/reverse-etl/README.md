# Reverse ETL

Sync Delta Lake tables from the Lakehouse into Lakebase for low-latency serving.

## Labs

| Order | Lab | What You'll Learn |
|-------|-----|-------------------|
| 1 | `Reverse_ETL` | Set up a synced table, monitor sync status, observe incremental changes |
| 2 | `create_synced_table` | Minimal standalone reference for synced table setup |

## Prerequisites

- Complete **`00_Setup_Lakebase_Project`** (foundation)

## Bring Your Own Data

The lab generates a sample Delta table by default, but you can sync any existing Delta table instead. Set `USE_OWN_DATA = True` in the configuration cell and point `SOURCE_TABLE` to your own table. The only requirement is that your table has **Change Data Feed** enabled.

If you don't have a table ready, the lab creates a catalog, schema, and sample data for you automatically.

## Key Concepts

- **Synced tables** — Automatic one-way sync from Delta Lake → Lakebase
- **Change Data Feed (CDF)** — Delta table feature that tracks row-level changes for incremental sync
- **Service Principal grants** — Required for the sync pipeline to write into Lakebase

## Notes

See `docs/PERMISSIONS.md` for the Service Principal grants needed for synced tables.
