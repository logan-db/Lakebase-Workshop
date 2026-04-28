# Workshop Facilitator Guide

## Overview

This guide helps facilitators run a Lakebase Autoscaling workshop. The workshop uses a **foundation + choose-your-track** model: participants complete a single setup notebook, then follow a track tailored to their role — or mix and match labs across tracks.

## Prerequisites Checklist

Before the workshop:

- [ ] Databricks workspace with Lakebase Autoscaling enabled
- [ ] Each participant has workspace access with permissions to create Lakebase projects
- [ ] Python 3.11+ installed on each participant's machine

## Workshop Structure

### Foundation (required — all participants)

| Notebook | Location | What It Does |
|----------|----------|--------------|
| `00_Setup_Lakebase_Project` | `notebooks/` | Create project, seed user schema (6 tables, 8 products) |

### Participant Tracks

After the foundation, participants follow a track based on their role. Each track is a recommended sequence of labs — but every lab is independent, so participants can skip ahead or explore across tracks.

#### Application Builders

*For developers building apps, APIs, and AI agents on Lakebase.*

| Order | Lab | Location | What It Covers |
|-------|-----|----------|----------------|
| 1 | Data Operations | `labs/data-operations/` | CRUD, JSONB, arrays, triggers, transactions |
| 2 | Agentic Memory | `labs/agentic-memory/` | Persistent AI agent memory with sessions |
| 3 | App Deployment *(capstone)* | `labs/app-deployment/` | Full-stack React + FastAPI Lab Console app |

**Key narrative:** *"Lakebase gives your applications a production-grade PostgreSQL backend inside the Lakehouse — no separate infrastructure, no bespoke sync pipelines."*

#### Data & ML Engineers

*For teams connecting the Lakehouse to operational workloads and ML serving.*

| Order | Lab | Location | What It Covers |
|-------|-----|----------|----------------|
| 1 | Reverse ETL | `labs/reverse-etl/` | Sync Delta Lake tables into Lakebase |
| 2 | Online Feature Store | `labs/online-feature-store/` | Real-time ML feature serving with Lakebase |
| 3 | Observability | `labs/observability/` | pg_stat views, index analysis, monitoring |

**Key narrative:** *"Your analytics data, served at OLTP speed — with native reverse ETL and a feature store that IS Lakebase."*

#### Platform Architects

*For central IT, infrastructure, and security teams evaluating Lakebase for production readiness.*

| Order | Lab | Location | What It Covers |
|-------|-----|----------|----------------|
| 1 | Development Experience | `labs/development-experience/` | Branching, autoscaling, scale-to-zero |
| 2 | Authentication | `labs/authentication/` | OAuth tokens, roles, two-layer permissions |
| 3 | Backup & Recovery | `labs/backup-recovery/` | PITR, branch snapshots, instant restore |

**Key narrative:** *"Fully managed PostgreSQL with Git-like branching, OAuth security, and instant recovery — governed by Unity Catalog."*

### All Labs Reference

Every lab lives directly in `labs/`. No track folder structure — tracks are a facilitation guide, not a file hierarchy.

| Lab | Location | What It Covers |
|-----|----------|----------------|
| Data Operations | `labs/data-operations/` | CRUD, JSONB, arrays, triggers, transactions |
| Reverse ETL | `labs/reverse-etl/` | Synced tables from Delta Lake |
| Development Experience | `labs/development-experience/` | Branching, autoscaling, scale-to-zero |
| Observability | `labs/observability/` | pg_stat views, index analysis, monitoring |
| Authentication | `labs/authentication/` | OAuth tokens, roles, permissions |
| Backup & Recovery | `labs/backup-recovery/` | PITR, branch snapshots, restore |
| Agentic Memory | `labs/agentic-memory/` | Persistent agent memory pattern |
| Online Feature Store | `labs/online-feature-store/` | Real-time ML feature serving with Lakebase |
| App Deployment | `labs/app-deployment/` | Full-stack Lab Console app (capstone) |

## Timing Options

### Full Workshop — Multi-Track (2.5 hours)

Best for mixed audiences. Everyone does the foundation together, then splits into tracks.

| Time | Activity | Details |
|------|----------|---------|
| 0:00 – 0:15 | **Introduction**: What is Lakebase? Architecture overview | Slides + foundation |
| 0:15 – 0:30 | **Setup**: Clone repo, run `setup.sh`, deploy content | Terminal |
| 0:30 – 0:45 | **Foundation**: Create Lakebase project + seed schema | `notebooks/00_Setup_Lakebase_Project` |
| 0:45 – 1:45 | **Track Time**: Participants follow their track (3 labs each) | See track tables above |
| 1:45 – 2:15 | **Cross-Track Exploration**: Try a lab from another track | Participant choice |
| 2:15 – 2:30 | **Wrap-up**: App Deployment overview, Q&A | `labs/app-deployment/` |

> **Facilitation tip:** Assign tracks at the start based on participant roles. Print or screen-share the track tables so participants know their sequence. Roaming facilitators can help across all three tracks simultaneously.

### Full Workshop — Single Track (2.5 hours)

Best for homogeneous audiences (e.g., all developers, all platform engineers). Run the foundation, then go deep on one track with time to explore others.

| Time | Activity | Details |
|------|----------|---------|
| 0:00 – 0:15 | **Introduction**: What is Lakebase? Architecture overview | Slides + foundation |
| 0:15 – 0:30 | **Setup**: Clone repo, run `setup.sh`, deploy content | Terminal |
| 0:30 – 0:45 | **Foundation**: Create Lakebase project + seed schema | `notebooks/00_Setup_Lakebase_Project` |
| 0:45 – 1:05 | **Track Lab 1** | First lab in the chosen track |
| 1:05 – 1:25 | **Track Lab 2** | Second lab in the chosen track |
| 1:25 – 1:45 | **Track Lab 3** | Third lab in the chosen track |
| 1:45 – 2:15 | **Bonus**: Explore labs from other tracks | Participant choice |
| 2:15 – 2:30 | **Wrap-up**: Q&A, next steps | Remaining paths as self-paced |

### Standard Workshop (90 min)

Pick one track and run it end-to-end.

| Time | Activity | Details |
|------|----------|---------|
| 0:00 – 0:10 | Introduction + architecture | Slides + foundation |
| 0:10 – 0:25 | Setup + Foundation | Terminal + `notebooks/00` |
| 0:25 – 0:45 | **Track Lab 1** | First lab in the chosen track |
| 0:45 – 1:05 | **Track Lab 2** | Second lab in the chosen track |
| 1:05 – 1:20 | **Track Lab 3** | Third lab in the chosen track |
| 1:20 – 1:30 | Wrap-up + Q&A | Remaining tracks as self-paced |

### Short Session (60 min)

Highlight one lab from each track to show breadth.

| Time | Activity | Details |
|------|----------|---------|
| 0:00 – 0:10 | Introduction + setup | Slides + terminal |
| 0:10 – 0:25 | **Foundation** | `notebooks/00` |
| 0:25 – 0:40 | **Development Experience** (Branching) | Platform Architects track highlight |
| 0:40 – 0:55 | **Data Operations** (CRUD + JSONB) | Application Builders track highlight |
| 0:55 – 1:00 | Wrap-up, point to full tracks for self-paced | All tracks |

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

Each participant opens `notebooks/00_Setup_Lakebase_Project` and clicks **Run All**. This creates their personal Lakebase project (`lakebase-lab-<username>`) and seeds a per-user schema (`lakebase_lab_<username>`).

### 4. Choose lab paths

Participants explore paths at their own pace. Each lab is self-contained — it installs its own dependencies and derives the project ID automatically.

For a guided workshop, direct participants to specific paths based on the timing options above.

### 5. (Optional) Deploy the Lab Console app

For the full interactive experience, follow `labs/app-deployment/Deploy_Lab_Console_App`. This requires:

1. Deploying via `databricks bundle deploy` (the pre-built frontend is included)
2. Adding the Lakebase database as a resource in the Apps UI
3. Granting SP permissions (see `docs/PERMISSIONS.md`)

## Demo Script

### Foundation — Architecture & Setup (all tracks)

1. Walk through the architecture diagrams (resource hierarchy, platform fit)
2. Run the project creation — takes ~2 min
3. Show the seeded tables and products
4. Key talking point: *"Fully managed PostgreSQL, no infrastructure to configure."*

---

### Application Builders Track

#### Data Operations — CRUD & JSONB

1. Run a JSONB metadata query (`metadata @> '{"brand": "SoundMax"}'`)
2. Show array filtering with `ANY` and `&&`
3. Insert → update → delete a product, then check the audit log
4. Run a transaction, show atomicity
5. Key talking point: *"Full PostgreSQL — JSONB, arrays, triggers, transactions."*

#### Agentic Memory

1. Create a session, store a multi-turn conversation
2. Query conversation history
3. Show cross-session JSONB queries
4. Key talking point: *"Persistent agent memory with no extra infrastructure."*

#### App Deployment (capstone)

1. Walk through the Lab Console architecture (React + FastAPI + Lakebase)
2. Show how the app connects via OAuth and the Databricks SDK
3. Key talking point: *"A full-stack app running on Databricks, backed by Lakebase — deployed in minutes."*

---

### Data & ML Engineers Track

#### Reverse ETL — Synced Tables

1. Create a Delta table with CDF enabled
2. Set up a synced table pointing to Lakebase
3. Check sync status
4. Key talking point: *"Your analytics lakehouse data, served at OLTP speed."*

#### Online Feature Store

1. Create a feature table with primary key and CDF
2. Provision an online store — show that it creates a Lakebase Autoscaling instance
3. Publish features, add new rows, re-publish
4. Connect directly to the online store via PostgreSQL
5. Key talking point: *"Your online feature store IS Lakebase — same managed PostgreSQL, optimized for ML serving."*
6. **Note:** Requires DBR 16.4 LTS ML or serverless. Online store provisioning takes 2–4 minutes.

#### Observability — Monitoring

1. Show database-level stats (cache hit %, connections, commits)
2. Walk through table-level activity (seq scans vs index scans)
3. Show index usage — point out any unused indexes
4. Show active connections
5. Key talking point: *"All standard PostgreSQL observability — plus the workspace monitoring UI."*

---

### Platform Architects Track

#### Development Experience — Branching

1. Show the production branch (default, protected)
2. Create `lab-dev-01` with a 24h TTL
3. Create a `reviews` table on the dev branch
4. Show it does NOT exist on production
5. Key talking point: *"This is like Git for your database — instant, isolated clones."*

#### Development Experience — Autoscaling

1. Show the production endpoint's current CU range
2. Walk through the CU sizing reference table
3. Explain the max 8 CU spread constraint
4. Mention scale-to-zero for non-production branches
5. Key talking point: *"You pay for what you use. Dev branches cost nothing when idle."*

#### Authentication — Tokens & Permissions

1. Generate a credential, decode the JWT
2. Show the 1-hour expiry and refresh pattern
3. List roles — show how identities map
4. Show connection details for external tools
5. Key talking point: *"No static passwords. OAuth tokens with automatic rotation."*

#### Backup & Recovery — PITR

1. Create a snapshot branch (instant)
2. Simulate disaster on a work branch (drop table)
3. Recover by branching from the snapshot
4. Explain PITR and the 35-day window
5. Key talking point: *"Backups are always on. Recovery is instant via branching."*

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
