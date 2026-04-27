# Online Feature Store

Use Lakebase Autoscaling as a high-performance online feature store for real-time ML serving — recommendation systems, fraud detection, and personalization engines.

## Labs

| Lab | What You'll Learn |
|-----|-------------------|
| `Online_Feature_Store` | Create feature tables, provision an online store, publish features, query via PostgreSQL |

## Prerequisites

- Complete **`00_Setup_Lakebase_Project`** (foundation)
- **DBR 16.4 LTS ML** or **serverless** compute
- A Unity Catalog catalog & schema with write access

## Key Concepts

- **Online Feature Store** — A managed Lakebase Autoscaling instance optimized for low-latency feature lookups
- **Feature table** — A Delta table in Unity Catalog with a primary key and Change Data Feed enabled
- **Publish modes** — TRIGGERED (on-demand sync), CONTINUOUS (streaming), or SNAPSHOT (full copy)
- **Feature Serving endpoints** — REST API endpoints that resolve features from online stores automatically
- **Lakebase under the hood** — The online store IS a Lakebase PostgreSQL instance, queryable with standard tools

## Architecture

```
Offline Feature Table (Delta/UC)
    │
    │  fe.publish_table()
    │  (TRIGGERED / CONTINUOUS / SNAPSHOT)
    ▼
Online Feature Store (Lakebase Autoscaling)
    │
    ├──→ Feature Serving Endpoint (REST API for real-time apps)
    │
    └──→ Direct PostgreSQL access (SQL editor, psycopg, etc.)
```

## Cost Notes

- Online stores incur costs continuously — delete them when not in use
- Start with `CU_1` for testing, scale up only when needed
- Multiple feature tables can share a single online store
