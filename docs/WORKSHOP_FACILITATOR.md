# Workshop Facilitator Guide

## Overview

This guide helps facilitators run a Lakebase Autoscaling workshop. The workshop uses a **foundation + choose-your-path** model: participants complete a single setup notebook, then explore independent lab paths based on their interest.

## Prerequisites Checklist

Before the workshop:

- [ ] Databricks workspace with Lakebase Autoscaling enabled
- [ ] Each participant has workspace access with permissions to create Lakebase projects
- [ ] Python 3.11+ installed on each participant's machine
- [ ] Node.js 18+ installed (only needed for the App Deployment path)

## Workshop Structure

### Foundation (required)

| Notebook | Location | What It Does |
|----------|----------|--------------|
| `00_Setup_Lakebase_Project` | `notebooks/` | Create project, seed demo schema (5 tables, 8 products) |

### Lab Paths (independent — pick based on audience)

| Path | Location | What It Covers |
|------|----------|----------------|
| Development Experience | `labs/development-experience/` | Branching, autoscaling, scale-to-zero |
| Data Operations | `labs/data-operations/` | CRUD, JSONB, arrays, triggers, transactions |
| Observability | `labs/observability/` | pg_stat views, index analysis, monitoring |
| Reverse ETL | `labs/reverse-etl/` | Synced tables from Delta Lake |
| Backup & Recovery | `labs/backup-recovery/` | PITR, branch snapshots, restore |
| Agentic Memory | `labs/agentic-memory/` | Persistent agent memory pattern |
| Authentication | `labs/authentication/` | OAuth tokens, roles, permissions |
| App Deployment | `labs/app-deployment/` | Full-stack Lab Console app (capstone) |

## Timing Options

### Full Workshop (2.5 hours)

| Time | Activity | Path / Resource |
|------|----------|-----------------|
| 0:00 – 0:15 | Introduction: What is Lakebase? Architecture overview | Slides + foundation |
| 0:15 – 0:30 | Setup: Clone repo, run `setup.sh`, deploy content | Terminal |
| 0:30 – 0:45 | **Foundation**: Create Lakebase project + seed schema | `notebooks/00_Setup_Lakebase_Project` |
| 0:45 – 1:05 | **Development Experience**: Branching + autoscaling | `labs/development-experience/` |
| 1:05 – 1:25 | **Data Operations**: CRUD, JSONB, transactions | `labs/data-operations/` |
| 1:25 – 1:40 | **Observability**: pg_stat views, monitoring | `labs/observability/` |
| 1:40 – 1:55 | **Backup & Recovery**: PITR, snapshots | `labs/backup-recovery/` |
| 1:55 – 2:15 | **Choose your own**: Reverse ETL, Agentic Memory, or Authentication | Participant choice |
| 2:15 – 2:30 | Wrap-up: App Deployment overview, Q&A | `labs/app-deployment/` |

### Standard Workshop (90 min)

| Time | Activity | Path / Resource |
|------|----------|-----------------|
| 0:00 – 0:10 | Introduction + architecture | Slides + foundation |
| 0:10 – 0:25 | Setup + foundation | Terminal + `notebooks/00` |
| 0:25 – 0:45 | **Development Experience** | `labs/development-experience/` |
| 0:45 – 1:05 | **Data Operations** | `labs/data-operations/` |
| 1:05 – 1:20 | **Choose one**: Observability, Backup, or Agentic Memory | Participant choice |
| 1:20 – 1:30 | Wrap-up + Q&A | Remaining paths as self-paced |

### Short Session (60 min)

| Time | Activity | Path / Resource |
|------|----------|-----------------|
| 0:00 – 0:10 | Introduction + setup | Slides + terminal |
| 0:10 – 0:25 | **Foundation** | `notebooks/00` |
| 0:25 – 0:45 | **Development Experience** (Branching only) | `labs/development-experience/Branches_and_Environments` |
| 0:45 – 0:55 | **Data Operations** (highlights) | `labs/data-operations/Data_Operations` |
| 0:55 – 1:00 | Wrap-up, point to remaining paths for self-paced | All paths |

## Step-by-Step Setup

### 1. Clone and configure (all participants)

```bash
git clone <this-repo-url>
cd Lakebase-Workshop
bash setup.sh
```

The script installs dependencies, authenticates the Databricks CLI, validates Lakebase access, and configures the bundle profile.

### 2. Deploy content to the workspace

**Option A — Deploy as a Declarative Automation Bundle (recommended):**

```bash
databricks bundle deploy --target dev --profile lakebase-workshop
```

Content appears at: **Workspace → Users → `<email>` → .bundle → lakebase-workshop → dev → files**

**Option B — Upload from the CLI:**

```bash
databricks workspace mkdirs "/Workspace/Users/<email>/lakebase-workshop" --profile lakebase-workshop

# Upload foundation
for nb in notebooks/*.py; do
  databricks workspace import \
    "/Workspace/Users/<email>/lakebase-workshop/$(basename $nb)" \
    --file "$nb" --format SOURCE --language PYTHON \
    --overwrite --profile lakebase-workshop
done

# Upload lab paths
for nb in labs/**/*.py; do
  dir=$(dirname "$nb" | sed 's|labs/||')
  databricks workspace mkdirs "/Workspace/Users/<email>/lakebase-workshop/labs/$dir" \
    --profile lakebase-workshop
  databricks workspace import \
    "/Workspace/Users/<email>/lakebase-workshop/labs/$dir/$(basename $nb)" \
    --file "$nb" --format SOURCE --language PYTHON \
    --overwrite --profile lakebase-workshop
done
```

### 3. Run the foundation

Each participant opens `notebooks/00_Setup_Lakebase_Project` and clicks **Run All**. This creates their personal Lakebase project (`lakebase-lab-<username>`) and seeds the demo schema.

### 4. Choose lab paths

Participants explore paths at their own pace. Each lab is self-contained — it installs its own dependencies and derives the project ID automatically.

For a guided workshop, direct participants to specific paths based on the timing options above.

### 5. (Optional) Deploy the Lab Console app

For the full interactive experience, follow `labs/app-deployment/Deploy_Lab_Console_App`. This requires:

1. Building the React frontend (`bash apps/lakebase-lab-console/build.sh`)
2. Deploying via `databricks bundle deploy`
3. Adding the Lakebase database as a resource in the Apps UI
4. Granting SP permissions (see `docs/PERMISSIONS.md`)

## Demo Script

### Foundation — Architecture & Setup

1. Walk through the architecture diagrams (resource hierarchy, platform fit)
2. Run the project creation — takes ~2 min
3. Show the seeded tables and products
4. Key talking point: *"Fully managed PostgreSQL, no infrastructure to configure."*

### Development Experience — Branching

1. Show the production branch (default, protected)
2. Create `lab-dev-01` with a 24h TTL
3. Create a `reviews` table on the dev branch
4. Show it does NOT exist on production
5. Key talking point: *"This is like Git for your database — instant, isolated clones."*

### Development Experience — Autoscaling

1. Show the production endpoint's current CU range
2. Walk through the CU sizing reference table
3. Explain the max 8 CU spread constraint
4. Mention scale-to-zero for non-production branches
5. Key talking point: *"You pay for what you use. Dev branches cost nothing when idle."*

### Authentication — Tokens & Permissions

1. Generate a credential, decode the JWT
2. Show the 1-hour expiry and refresh pattern
3. List roles — show how identities map
4. Show connection details for external tools
5. Key talking point: *"No static passwords. OAuth tokens with automatic rotation."*

### Data Operations — CRUD & JSONB

1. Run a JSONB metadata query (`metadata @> '{"brand": "SoundMax"}'`)
2. Show array filtering with `ANY` and `&&`
3. Insert → update → delete a product, then check the audit log
4. Run a transaction, show atomicity
5. Key talking point: *"Full PostgreSQL — JSONB, arrays, triggers, transactions."*

### Observability — Monitoring

1. Show database-level stats (cache hit %, connections, commits)
2. Walk through table-level activity (seq scans vs index scans)
3. Show index usage — point out any unused indexes
4. Show active connections
5. Key talking point: *"All standard PostgreSQL observability — plus the workspace monitoring UI."*

### Reverse ETL — Synced Tables

1. Create a Delta table with CDF enabled
2. Set up a synced table pointing to Lakebase
3. Check sync status
4. Key talking point: *"Your analytics lakehouse data, served at OLTP speed."*

### Backup & Recovery — PITR

1. Create a snapshot branch (instant)
2. Simulate disaster on a work branch (drop table)
3. Recover by branching from the snapshot
4. Explain PITR and the 35-day window
5. Key talking point: *"Backups are always on. Recovery is instant via branching."*

### Agentic Memory

1. Create a session, store a multi-turn conversation
2. Query conversation history
3. Show cross-session JSONB queries
4. Key talking point: *"Persistent agent memory with no extra infrastructure."*

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `setup.sh` fails at auth | Run `databricks auth login --host <url> --profile lakebase-workshop` manually |
| Foundation hangs on "Waiting for endpoint" | Endpoint creation can take 2–3 minutes. Let it run. |
| "password authentication failed" | Token expired (1h TTL). Re-run the connection cell. |
| "permission denied for table" | Run the GRANT statements from `docs/PERMISSIONS.md` |
| Lab Console shows "Loading..." forever | Check `/api/dbtest` — likely missing DB resource or SP permissions |

## Cleanup

Participants can delete their projects by uncommenting the cleanup cell at the bottom of the foundation notebook, or by running:

```python
from databricks.sdk import WorkspaceClient
w = WorkspaceClient()
w.postgres.delete_project(name="projects/lakebase-lab-<username>")
```

Or leave them running — branches with TTLs will auto-expire.
