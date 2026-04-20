# Lab Paths

After completing the **foundation** (`notebooks/00_Setup_Lakebase_Project`), choose any of these paths based on your interest. Each path is independent — pick one, pick several, or do them all.

## Available Paths

| Path | Folder | What You'll Explore |
|------|--------|---------------------|
| [Development Experience](development-experience/) | `development-experience/` | Git-like branching, autoscaling compute, scale-to-zero |
| [Data Operations](data-operations/) | `data-operations/` | CRUD, JSONB, arrays, audit triggers, transactions, advanced SQL |
| [Reverse ETL](reverse-etl/) | `reverse-etl/` | Sync Delta Lake tables into Lakebase for low-latency serving |
| [Observability](observability/) | `observability/` | pg_stat views, index analysis, connection monitoring |
| [Backup & Recovery](backup-recovery/) | `backup-recovery/` | Point-in-time recovery, branch snapshots, instant restore |
| [Agentic Memory](agentic-memory/) | `agentic-memory/` | Persistent AI agent memory with session/message storage |
| [Authentication](authentication/) | `authentication/` | OAuth tokens, two-layer permissions, role grants |
| [App Deployment](app-deployment/) | `app-deployment/` | Full-stack React + FastAPI app using Lakebase (capstone) |

## Path Dependencies

Most paths only require the foundation. A few have soft recommendations:

```
Foundation (00_Setup)
    │
    ├── Development Experience
    ├── Data Operations
    │       └── (recommended before) Observability
    ├── Reverse ETL
    ├── Backup & Recovery
    ├── Agentic Memory
    ├── Authentication
    └── App Deployment (best after exploring other paths)
```

## Suggested Combinations

| Goal | Paths |
|------|-------|
| **Quick overview (30 min)** | Development Experience |
| **Data-focused (60 min)** | Data Operations → Observability |
| **App builder (60 min)** | Authentication → Agentic Memory → App Deployment |
| **Platform deep-dive (90 min)** | Development Experience → Backup & Recovery → Observability |
| **Full workshop (2.5 hours)** | All paths |
