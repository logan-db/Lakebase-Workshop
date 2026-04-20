# Lakebase Autoscaling Workshop

A hands-on workshop for exploring **Databricks Lakebase Autoscaling** — a fully managed, serverless PostgreSQL database with autoscaling compute, Git-like branching, scale-to-zero, and instant point-in-time recovery.

## Workshop Structure

This workshop follows a **foundation + choose-your-path** model:

```
                    ┌───────────────────────────────┐
                    │   00_Setup_Lakebase_Project    │
                    │      (Foundation — required)   │
                    └───────────────┬───────────────┘
                                    │
         ┌──────────────────────────┼──────────────────────────┐
         │                          │                          │
         ▼                          ▼                          ▼
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│ 1. Data         │      │ 2. Reverse ETL  │      │ 3. Development  │
│    Operations   │      │                 │      │    Experience   │
│ ─────────────── │      │ ─────────────── │      │ ─────────────── │
│ • CRUD/JSONB    │      │ • Synced Tables │      │ • Branching     │
│ • Transactions  │      │ • Delta → PG    │      │ • Autoscaling   │
│ • Advanced SQL  │      │                 │      │ • Scale-to-zero │
└─────────────────┘      └─────────────────┘      └─────────────────┘

┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│ 4. Observability│      │ 5. Auth &       │      │ 6. Backup &     │
│                 │      │    Permissions  │      │    Recovery     │
│ ─────────────── │      │ ─────────────── │      │ ─────────────── │
│ • pg_stat views │      │ • OAuth tokens  │      │ • PITR          │
│ • Index usage   │      │ • Roles/grants  │      │ • Snapshots     │
│ • Monitoring    │      │ • External tools│      │ • Restore       │
└─────────────────┘      └─────────────────┘      └─────────────────┘

┌─────────────────┐      ┌─────────────────┐
│ 7. Agentic      │      │ 8. App          │
│    Memory       │      │    Deployment   │
│ ─────────────── │      │ ─────────────── │
│ • Sessions      │      │ • React +       │
│ • Multi-turn    │      │   FastAPI       │
│ • JSONB context │      │ • Full-stack    │
└─────────────────┘      │   (capstone)    │
                         └─────────────────┘
```

### Foundation (required)

Run this first — it creates your Lakebase project and seeds the demo schema:

| Notebook | What It Does |
|----------|--------------|
| `notebooks/00_Setup_Lakebase_Project` | Create project, wait for endpoint, seed 5 tables with sample data |

### Lab Paths (choose your adventure)

After completing the foundation, pick any path based on your interest. Each path is **independent** — no need to follow a specific order.

| # | Path | Folder | Labs | Description |
|---|------|--------|------|-------------|
| 1 | **Data Operations** | `labs/data-operations/` | Data Operations, Advanced SQL | CRUD, JSONB, arrays, triggers, transactions |
| 2 | **Reverse ETL** | `labs/reverse-etl/` | Reverse ETL | Sync Delta Lake tables into Lakebase |
| 3 | **Development Experience** | `labs/development-experience/` | Branches, Autoscaling | Branching, CU sizing, scale-to-zero |
| 4 | **Observability** | `labs/observability/` | Observability & Monitoring | pg_stat views, index analysis, monitoring |
| 5 | **Authentication** | `labs/authentication/` | Auth & Permissions | OAuth tokens, roles, two-layer permissions |
| 6 | **Backup & Recovery** | `labs/backup-recovery/` | Backup & Recovery | PITR, branch snapshots, instant restore |
| 7 | **Agentic Memory** | `labs/agentic-memory/` | Agent Memory | Persistent AI agent memory with sessions |
| 8 | **App Deployment** | `labs/app-deployment/` | Deploy Lab Console | Full-stack React + FastAPI app (capstone) |

Each path folder has its own `README.md` with detailed prerequisites and key concepts.

## Getting Started

### Prerequisites

- A Databricks workspace with **Lakebase Autoscaling** enabled
- Python 3.11+

### Step 1: Clone and set up

```bash
git clone <this-repo-url>
cd Lakebase-Workshop
bash setup.sh
```

The setup script walks you through:

1. **Install requirements?** (Y/n) — installs `databricks-sdk`, `psycopg`, and checks for the Databricks CLI
2. **Connect to your workspace** — enter your workspace URL or pick an existing profile. Opens your browser to authenticate.
3. **Validate** — confirms Lakebase is available on your workspace
4. **Next steps** — shows you exactly what to do next, including the workspace paths

No prior Databricks CLI setup is needed. The script handles everything.

### Step 2: Deploy to your workspace

After setup completes, choose one of these paths:

**Option A: Deploy as a Declarative Automation Bundle (recommended)**

```bash
# From the repo root:
databricks bundle deploy --target dev --profile lakebase-workshop
```

Then in the Databricks UI, find your content at:
**Workspace → Users → `<your-email>` → .bundle → lakebase-workshop → dev → files**

**Option B: Upload from the CLI**

```bash
# Create the workspace folder
databricks workspace mkdirs "/Workspace/Users/<your-email>/lakebase-workshop" \
  --profile lakebase-workshop

# Upload foundation notebook
for nb in notebooks/*.py; do
  databricks workspace import \
    "/Workspace/Users/<your-email>/lakebase-workshop/$(basename $nb)" \
    --file "$nb" --format SOURCE --language PYTHON \
    --overwrite --profile lakebase-workshop
done

# Upload lab paths
for nb in labs/**/*.py; do
  dir=$(dirname "$nb" | sed 's|labs/||')
  databricks workspace mkdirs "/Workspace/Users/<your-email>/lakebase-workshop/labs/$dir" \
    --profile lakebase-workshop
  databricks workspace import \
    "/Workspace/Users/<your-email>/lakebase-workshop/labs/$dir/$(basename $nb)" \
    --file "$nb" --format SOURCE --language PYTHON \
    --overwrite --profile lakebase-workshop
done
```

### Step 3: Run the foundation

Open **`00_Setup_Lakebase_Project`** and click **Run All**. It creates your Lakebase project, waits for the endpoint, and seeds the demo schema.

### Step 4: Pick a path

Browse the paths in `labs/` and pick whichever interests you. Each lab notebook is self-contained — it installs its own dependencies and derives the project ID automatically.

**Suggested starting points by role:**

| Role | Recommended Paths |
|------|-------------------|
| **Data Engineer** | Data Operations → Reverse ETL → Observability |
| **Platform Engineer** | Development Experience → Observability → Backup & Recovery |
| **App Developer** | Data Operations → Agentic Memory → App Deployment |
| **Quick Overview** | Data Operations → Development Experience |

## Lab Console App

The `apps/lakebase-lab-console/` folder contains an interactive **React + FastAPI** application that ties together every feature from the lab paths into a single UI:

| Module | Feature |
|--------|---------|
| Branch Manager | Create/delete branches from the UI |
| Autoscaling Dashboard | Resize compute and monitor CU ranges |
| Load Tester | Generate synthetic traffic, stream live metrics |
| Data Playground | CRUD operations, audit log viewer |
| Reverse ETL | Synced table status |
| API Tester | Raw SQL execution against any branch |
| Agent Memory | Session/message management |

## Architecture

```
Browser (React Lab Console)
    |
    v
FastAPI Backend (Databricks App)
    |
    +---> Databricks SDK (w.postgres) -- branch/endpoint management
    |
    +---> psycopg3 (PostgreSQL wire) -- CRUD, load test, agent memory
    |
    v
Lakebase Autoscaling (PostgreSQL)
    Project > Branch > Endpoint
```

## Repository Structure

```
Lakebase-Workshop/
├── setup.sh                                    # ← Start here
├── databricks.yml                              # DAB bundle config
├── notebooks/                                  # Foundation (run first)
│   └── 00_Setup_Lakebase_Project.py
├── labs/                                       # Lab paths (pick your adventure)
│   ├── _setup.py                               # Shared setup (auto-loaded by each lab)
│   ├── README.md                               # Path index
│   ├── development-experience/                 # Branching + Autoscaling
│   │   ├── Branches_and_Environments.py
│   │   └── Autoscaling_and_Compute.py
│   ├── data-operations/                        # CRUD, JSONB, Advanced SQL
│   │   ├── Data_Operations.py
│   │   └── Advanced_Postgres.sql
│   ├── reverse-etl/                            # Synced tables from Delta
│   │   └── Reverse_ETL.py
│   ├── observability/                          # pg_stat views, monitoring
│   │   └── Observability_and_Monitoring.py
│   ├── backup-recovery/                        # PITR, snapshots
│   │   └── Backup_and_Recovery.py
│   ├── agentic-memory/                         # Agent memory pattern
│   │   └── Agent_Memory.py
│   ├── authentication/                         # OAuth, roles, permissions
│   │   └── Authentication_and_Permissions.py
│   └── app-deployment/                         # Lab Console (capstone)
│       └── Deploy_Lab_Console_App.py
├── apps/lakebase-lab-console/                  # Lab Console app
│   ├── backend/                                # FastAPI routes & connection manager
│   ├── frontend/                               # React (Vite) UI
│   └── app.yaml                                # Databricks Apps config
├── bootstrap/
│   ├── seed.sql                                # Demo schema DDL (used by notebook 00)
│   └── requirements.txt                        # Python deps for local use
└── docs/
    ├── WORKSHOP_FACILITATOR.md
    ├── PERMISSIONS.md
    └── CREDITS.md
```

## Resources

- [Databricks Lakebase Documentation](https://docs.databricks.com/en/lakebase/index.html)
- [Databricks Apps Documentation](https://docs.databricks.com/en/dev-tools/databricks-apps/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)

## Credits

See [docs/CREDITS.md](docs/CREDITS.md) for attribution.
