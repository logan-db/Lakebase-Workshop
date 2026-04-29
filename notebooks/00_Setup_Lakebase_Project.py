# Databricks notebook source
# MAGIC %md
# MAGIC # 00 — Set Up Your Lakebase Autoscaling Project
# MAGIC
# MAGIC This notebook creates your Lakebase Autoscaling project, waits for the
# MAGIC endpoint to become active, and seeds a per-user schema with sample data.
# MAGIC
# MAGIC **Run this notebook once** before starting any of the workshop labs.
# MAGIC
# MAGIC ### What gets created
# MAGIC | Resource | Details |
# MAGIC |----------|---------|
# MAGIC | **Project** | `lakebase-lab-<your-username>` |
# MAGIC | **Branch** | `production` (auto-created, default) |
# MAGIC | **Compute** | Autoscaling endpoint (0.5+ CU) |
# MAGIC | **Schema** | `lakebase_lab_<your_username>` with 6 tables: products, events, agent_sessions, agent_messages, agent_memory_store, audit_log |
# MAGIC | **Sample data** | 8 products with JSONB metadata, array tags, and audit triggers |

# COMMAND ----------

# MAGIC %md
# MAGIC ## Lakebase Architecture
# MAGIC
# MAGIC Lakebase Autoscaling is Databricks' fully managed **PostgreSQL** service
# MAGIC for operational (OLTP) workloads. It runs inside your Databricks workspace
# MAGIC and is governed by Unity Catalog.
# MAGIC
# MAGIC ### Resource Hierarchy
# MAGIC
# MAGIC ```
# MAGIC Databricks Workspace
# MAGIC └── Lakebase Project (top-level container)
# MAGIC     └── Branch(es) (isolated database environments, like Git branches)
# MAGIC         ├── Compute Endpoint (autoscaling PostgreSQL server, 0.5–112 CU)
# MAGIC         ├── Database: databricks_postgres (default)
# MAGIC         │   └── Schema(s) → Tables, indexes, triggers, functions
# MAGIC         └── Roles (mapped to Databricks users / Service Principals)
# MAGIC ```
# MAGIC
# MAGIC ### Key Capabilities
# MAGIC
# MAGIC | Capability | Details |
# MAGIC |------------|---------|
# MAGIC | **Autoscaling Compute** | 0.5–112 CU (~1–224 GB RAM), scales based on load |
# MAGIC | **Scale-to-Zero** | Non-production branches suspend after inactivity |
# MAGIC | **Copy-on-Write Branching** | Instant isolated database clones for dev/test/CI |
# MAGIC | **Point-in-Time Recovery** | Restore to any moment within the configured window (up to 35 days) |
# MAGIC | **OAuth Authentication** | Token-based auth via Databricks SDK (1-hour token TTL) |
# MAGIC | **Reverse ETL** | Sync Delta Lake tables into PostgreSQL via synced tables |
# MAGIC | **Unity Catalog Integration** | Projects and access governed by workspace IAM |
# MAGIC
# MAGIC **Docs:** [What is Lakebase Autoscaling?](https://docs.databricks.com/aws/en/oltp/projects/about) |
# MAGIC [Get started with Lakebase](https://docs.databricks.com/aws/en/oltp/projects/get-started)
# MAGIC
# MAGIC ### How It Fits in the Databricks Platform
# MAGIC
# MAGIC ```
# MAGIC ┌─────────────────────────────────────────────────────┐
# MAGIC │                  Databricks Workspace               │
# MAGIC │                                                     │
# MAGIC │  ┌──────────┐  ┌──────────┐  ┌──────────────────┐  │
# MAGIC │  │  Delta    │  │  Model   │  │  Lakebase        │  │
# MAGIC │  │  Lake     │──│  Serving │  │  (PostgreSQL)    │  │
# MAGIC │  │  (OLAP)   │  │  (AI)    │  │  (OLTP)          │  │
# MAGIC │  └──────────┘  └──────────┘  └──────────────────┘  │
# MAGIC │       │              │               ▲              │
# MAGIC │       │         ┌────┘               │              │
# MAGIC │       ▼         ▼                    │              │
# MAGIC │  ┌──────────────────┐    ┌───────────────────┐      │
# MAGIC │  │  Databricks Apps │───▶│  Synced Tables     │      │
# MAGIC │  │  (Full-stack)    │    │  (Reverse ETL)     │      │
# MAGIC │  └──────────────────┘    └───────────────────┘      │
# MAGIC └─────────────────────────────────────────────────────┘
# MAGIC ```
# MAGIC
# MAGIC - **Delta Lake** stores your analytical data (OLAP)
# MAGIC - **Lakebase** serves operational data at low latency (OLTP)
# MAGIC - **Synced Tables** bridge the two via Reverse ETL
# MAGIC - **Databricks Apps** connect to Lakebase as a backend database

# COMMAND ----------

# MAGIC %pip install "databricks-sdk>=0.81.0" "psycopg[binary]>=3.0" --quiet

# COMMAND ----------

dbutils.library.restartPython()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 1: Configure
# MAGIC The project ID is derived from your username automatically.
# MAGIC Only change this if you want a custom name.

# COMMAND ----------

import re
from databricks.sdk import WorkspaceClient

w = WorkspaceClient()
user_email = w.current_user.me().user_name

def sanitize(email):
    name = email.split("@")[0]
    name = re.sub(r"[^a-z0-9-]", "-", name.lower())
    return re.sub(r"-+", "-", name).strip("-")

PROJECT_ID = f"lakebase-lab-{sanitize(user_email)}"
PG_SCHEMA  = f"lakebase_lab_{sanitize(user_email).replace('-', '_')}"
PG_VERSION = "17"

print(f"User:       {user_email}")
print(f"Project ID: {PROJECT_ID}")
print(f"PG Schema:  {PG_SCHEMA}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 2: Create the Lakebase Project
# MAGIC This creates the project and waits for the production endpoint to be ready.
# MAGIC Takes 1-3 minutes.

# COMMAND ----------

from databricks.sdk.service.postgres import Project, ProjectSpec
import time

try:
    existing = w.postgres.get_project(name=f"projects/{PROJECT_ID}")
    print(f"Project already exists: {existing.name}")
    print(f"Display name: {existing.status.display_name}")
except Exception:
    print(f"Creating project: {PROJECT_ID} ...")
    operation = w.postgres.create_project(
        project=Project(
            spec=ProjectSpec(
                display_name=f"Lakebase Workshop: {PROJECT_ID}",
                pg_version=PG_VERSION,
            )
        ),
        project_id=PROJECT_ID,
    )
    result = operation.wait()
    print(f"✓ Project created: {result.name}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 3: Wait for the Endpoint
# MAGIC The production branch gets a compute endpoint automatically. We need to
# MAGIC wait for it to become `ACTIVE` before we can connect.

# COMMAND ----------

print("Waiting for production endpoint to become active...")

endpoint = None
for attempt in range(90):
    try:
        endpoints = list(w.postgres.list_endpoints(
            parent=f"projects/{PROJECT_ID}/branches/production"
        ))
        if endpoints:
            ep = w.postgres.get_endpoint(name=endpoints[0].name)
            state = str(getattr(ep.status, "current_state", ""))
            if "ACTIVE" in state.upper():
                endpoint = ep
                print(f"✓ Endpoint is active!")
                print(f"  Host: {ep.status.hosts.host}")
                print(f"  Name: {ep.name}")
                break
            print(f"  State: {state} (attempt {attempt + 1})...")
    except Exception as e:
        print(f"  Waiting... ({e})")
    time.sleep(5)

if not endpoint:
    raise TimeoutError("Endpoint did not become active within 7.5 minutes. Check the Lakebase UI.")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 4: Connect and Seed the Schema
# MAGIC Creates 6 tables, indexes, audit triggers, and inserts 8 sample products
# MAGIC in a per-user schema (`lakebase_lab_<your_username>`).

# COMMAND ----------

import psycopg

host = endpoint.status.hosts.host
cred = w.postgres.generate_database_credential(endpoint=endpoint.name)
username = user_email

params = {"host": host, "dbname": "databricks_postgres", "user": username, "password": cred.token, "sslmode": "require"}
conn = psycopg.connect(**params)
print(f"✓ Connected to Lakebase")

# COMMAND ----------

import os

notebook_path = dbutils.notebook.entry_point.getDbutils().notebook().getContext().notebookPath().get()
project_root = os.path.dirname(os.path.dirname(f"/Workspace{notebook_path}"))
seed_path = os.path.join(project_root, "bootstrap", "seed.sql")

with open(seed_path) as f:
    SEED_SQL = f.read().replace("{schema}", PG_SCHEMA)

print(f"Loaded seed SQL from: bootstrap/seed.sql ({len(SEED_SQL)} chars)")
print(f"Target schema: {PG_SCHEMA}")

with conn.cursor() as cur:
    cur.execute(SEED_SQL)
conn.commit()
print(f"✓ Schema {PG_SCHEMA} created and seeded")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 5: Verify

# COMMAND ----------

from psycopg.rows import dict_row

cred = w.postgres.generate_database_credential(endpoint=endpoint.name)
params["password"] = cred.token

with psycopg.connect(**params, row_factory=dict_row) as verify_conn:
    with verify_conn.cursor() as cur:
        cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = %s ORDER BY table_name", [PG_SCHEMA])
        tables = [r["table_name"] for r in cur.fetchall()]
        print(f"Tables in {PG_SCHEMA} schema: {tables}")

        cur.execute(f"SELECT count(*) as cnt FROM {PG_SCHEMA}.products")
        cnt = cur.fetchone()["cnt"]
        print(f"Products seeded: {cnt}")

        cur.execute("SELECT version()")
        ver = cur.fetchone()["version"]
        print(f"PostgreSQL: {ver}")

conn.close()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 6: Attach Database to Lab Console App
# MAGIC Adds the Lakebase database as a resource on the Lab Console app so the app
# MAGIC can connect automatically via injected `PGHOST`/`PGUSER` environment variables.

# COMMAND ----------

import json

app_name = PROJECT_ID  # app uses the same naming convention

branch_name = f"projects/{PROJECT_ID}/branches/production"

try:
    db_resp = w.api_client.do(
        "GET",
        f"/api/2.0/postgres/{branch_name}/databases",
    )
    databases = db_resp.get("databases", [])
    db_resource = next(
        (d for d in databases if d.get("status", {}).get("postgres_database") == "databricks_postgres"),
        None,
    )
    if not db_resource:
        raise ValueError("databricks_postgres database not found on production branch")

    db_name = db_resource["name"]

    w.api_client.do(
        "PATCH",
        f"/api/2.0/apps/{app_name}",
        body={
            "resources": [
                {
                    "name": "lakebase-db",
                    "postgres": {
                        "branch": branch_name,
                        "database": db_name,
                        "permission": "CAN_CONNECT_AND_CREATE",
                    },
                }
            ]
        },
    )
    print(f"✓ Attached Lakebase database to app '{app_name}'")
    print(f"  Branch:   {branch_name}")
    print(f"  Database: {db_name}")

    # Grant the app's service principal access to the user's schema
    app_info = w.api_client.do("GET", f"/api/2.0/apps/{app_name}")
    sp_client_id = app_info.get("service_principal_client_id", "")
    if sp_client_id:
        cred2 = w.postgres.generate_database_credential(endpoint=endpoint.name)
        grant_params = {**params, "password": cred2.token}
        grant_conn = psycopg.connect(**grant_params)
        grant_conn.autocommit = True
        with grant_conn.cursor() as gcur:
            gcur.execute(f'GRANT USAGE, CREATE ON SCHEMA {PG_SCHEMA} TO "{sp_client_id}"')
            gcur.execute(f'GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA {PG_SCHEMA} TO "{sp_client_id}"')
            gcur.execute(f'GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA {PG_SCHEMA} TO "{sp_client_id}"')
            gcur.execute(f'ALTER DEFAULT PRIVILEGES IN SCHEMA {PG_SCHEMA} GRANT ALL ON TABLES TO "{sp_client_id}"')
            gcur.execute(f'ALTER DEFAULT PRIVILEGES IN SCHEMA {PG_SCHEMA} GRANT ALL ON SEQUENCES TO "{sp_client_id}"')
        grant_conn.close()
        print(f"✓ Granted schema access to app service principal")
    else:
        print(f"⚠ Could not determine app service principal — grant permissions manually")

except Exception as e:
    print(f"⚠ Could not attach database to app: {e}")
    print(f"  If you deployed without the app, this is expected.")
    print(f"  To deploy the app later, run from the repo root:")
    print(f"    databricks bundle run lakebase_lab_console --target dev")
    print(f"  Then re-run this cell to attach the database.")

# COMMAND ----------

# MAGIC %md
# MAGIC ## ✓ Setup Complete!
# MAGIC
# MAGIC Your Lakebase project is ready. Here's your configuration:

# COMMAND ----------

print("=" * 60)
print("  WORKSHOP CONFIGURATION")
print("=" * 60)
print(f"  Project ID:    {PROJECT_ID}")
print(f"  Endpoint:      {endpoint.name}")
print(f"  Host:          {endpoint.status.hosts.host}")
print(f"  Database:      databricks_postgres")
print(f"  Schema:        {PG_SCHEMA}")
print(f"  Username:      {user_email}")
print("=" * 60)
print()
print("  The Lab Console app auto-discovers the project ID and schema")
print("  from the attached database resource. No manual config needed.")

# COMMAND ----------

# MAGIC %md
# MAGIC ## What's Next?
# MAGIC
# MAGIC Your Lakebase project is ready. Pick any lab path below — they're ordered from
# MAGIC foundational to advanced, but each one is independent. Start wherever interests you most.
# MAGIC
# MAGIC | | Path | Folder | What You'll Learn |
# MAGIC |---|------|--------|-------------------|
# MAGIC | 1 | **Data Operations** | `labs/data-operations/` | CRUD, JSONB queries, array operators, audit triggers, transactions |
# MAGIC | 2 | **Reverse ETL** | `labs/reverse-etl/` | Sync Delta Lake tables into Lakebase for low-latency serving |
# MAGIC | 3 | **Development Experience** | `labs/development-experience/` | Git-like branching, autoscaling compute, scale-to-zero |
# MAGIC | 4 | **Observability** | `labs/observability/` | pg_stat views, index analysis, connection monitoring |
# MAGIC | 5 | **Authentication** | `labs/authentication/` | OAuth tokens, two-layer permissions, role grants |
# MAGIC | 6 | **Backup & Recovery** | `labs/backup-recovery/` | Point-in-time recovery, branch snapshots, instant restore |
# MAGIC | 7 | **Agentic Memory** | `labs/agentic-memory/` | Persistent AI agent memory with session/message storage |
# MAGIC | 8 | **Online Feature Store** | `labs/online-feature-store/` | Real-time ML feature serving powered by Lakebase |
# MAGIC | 9 | **App Deployment** | `labs/app-deployment/` | Full-stack React + FastAPI app using Lakebase (capstone) |

# COMMAND ----------

# MAGIC %md
# MAGIC ## (Optional) Clean Up
# MAGIC
# MAGIC Uncomment and run the cell below to delete your project when you're done.
# MAGIC **This permanently deletes all branches and data.**

# COMMAND ----------

# UNCOMMENT TO DELETE:
# w.postgres.delete_project(name=f"projects/{PROJECT_ID}")
# print(f"Project {PROJECT_ID} deletion initiated.")
