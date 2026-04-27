# Databricks notebook source
# MAGIC %md
# MAGIC # Deploy the Lab Console App
# MAGIC
# MAGIC **Path:** App Deployment &nbsp;|&nbsp; **Prerequisite:** `00_Setup_Lakebase_Project`
# MAGIC
# MAGIC **Lakebase feature:** Full-stack app using Lakebase as the backend
# MAGIC
# MAGIC This notebook walks you through deploying the **Lakebase Lab Console** —
# MAGIC an interactive React + FastAPI application that ties together every feature
# MAGIC from the workshop labs into a single UI.
# MAGIC
# MAGIC **What the Lab Console includes:**
# MAGIC - Branch Manager — create/delete branches from the UI
# MAGIC - Autoscaling Dashboard — resize compute and monitor CU ranges
# MAGIC - Load Tester — generate synthetic traffic and stream live metrics
# MAGIC - Data Playground — CRUD operations, audit log viewer
# MAGIC - Reverse ETL — check synced table status
# MAGIC - API Tester — raw SQL execution against any branch
# MAGIC - Agent Memory — session/message management UI

# COMMAND ----------

# MAGIC %md
# MAGIC ## Prerequisites
# MAGIC
# MAGIC 1. **`setup.sh` was run** — this deploys all notebooks, labs, and the Lab Console app via a Databricks Asset Bundle
# MAGIC 2. **Notebook `00` was run** — your Lakebase project exists and the demo schema is seeded
# MAGIC 3. **Lakebase database added as app resource** — after notebook 00, add the postgres resource to the app
# MAGIC    (Compute → Apps → lakebase-lab-console → Edit → Add Resource → Database)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Deployment
# MAGIC
# MAGIC If you ran `setup.sh` and chose **Yes** when prompted to deploy, the Lab Console
# MAGIC app is already deployed to your workspace via the Declarative Automation Bundle.
# MAGIC
# MAGIC To redeploy or deploy manually, run from the **repo root**:
# MAGIC
# MAGIC ```bash
# MAGIC databricks bundle deploy --target dev
# MAGIC ```
# MAGIC
# MAGIC Then open the app: **Compute → Apps → lakebase-lab-console**

# COMMAND ----------

# MAGIC %md
# MAGIC ## App Configuration Reference
# MAGIC
# MAGIC The app uses `app.yaml` for its configuration:
# MAGIC
# MAGIC ```yaml
# MAGIC command:
# MAGIC   - python
# MAGIC   - -m
# MAGIC   - uvicorn
# MAGIC   - app:app
# MAGIC   - --host
# MAGIC   - 0.0.0.0
# MAGIC   - --port
# MAGIC   - "8000"
# MAGIC env:
# MAGIC   - name: LAKEBASE_PROJECT_ID
# MAGIC     value: <your-project-id>
# MAGIC   - name: LAKEBASE_BRANCH_ID
# MAGIC     value: production
# MAGIC   - name: LAKEBASE_SCHEMA
# MAGIC     value: demo
# MAGIC resources:
# MAGIC   - name: lakebase-db
# MAGIC     type: postgres
# MAGIC ```
# MAGIC
# MAGIC After running notebook `00`, update `LAKEBASE_PROJECT_ID` in `app.yaml` with
# MAGIC your project ID (format: `lakebase-lab-<your-username>`).

# COMMAND ----------

# MAGIC %md
# MAGIC ## Service Principal Permissions
# MAGIC
# MAGIC When the app deploys, Databricks creates a Service Principal (SP) to run it.
# MAGIC You must create an OAuth-enabled Postgres role for the SP and grant it access
# MAGIC to your Lakebase tables.
# MAGIC
# MAGIC 1. Find the SP's `client_id` — the code cell below retrieves it automatically via the SDK,
# MAGIC    or you can find it manually in the App Environment tab (`DATABRICKS_CLIENT_ID`)
# MAGIC 2. Run the setup below to create the OAuth role and grant permissions
# MAGIC
# MAGIC ### Where to run the SQL
# MAGIC
# MAGIC You can execute these SQL statements from:
# MAGIC
# MAGIC - **Lakebase SQL Editor** — open the SQL editor in the Databricks UI for your Lakebase instance
# MAGIC - **This notebook** — use the code cell below if you're connected to the Lakebase instance
# MAGIC - **psql / any PostgreSQL client** — connect with your endpoint host and credentials
# MAGIC
# MAGIC ### Step 1: Create the OAuth role
# MAGIC
# MAGIC The `databricks_auth` extension enables OAuth authentication so the SP can
# MAGIC connect using Databricks-managed tokens instead of passwords.
# MAGIC See [Connect a Databricks App to Lakebase](https://docs.databricks.com/aws/en/oltp/projects/tutorial-databricks-apps-autoscaling).
# MAGIC
# MAGIC ```sql
# MAGIC CREATE EXTENSION IF NOT EXISTS databricks_auth;
# MAGIC SELECT databricks_create_role('<SP_CLIENT_ID>', 'service_principal');
# MAGIC ```
# MAGIC
# MAGIC ### Step 2: Grant schema and object access
# MAGIC
# MAGIC ```sql
# MAGIC GRANT ALL ON SCHEMA demo TO "<SP_CLIENT_ID>";
# MAGIC GRANT ALL ON ALL TABLES IN SCHEMA demo TO "<SP_CLIENT_ID>";
# MAGIC GRANT ALL ON ALL SEQUENCES IN SCHEMA demo TO "<SP_CLIENT_ID>";
# MAGIC ALTER DEFAULT PRIVILEGES IN SCHEMA demo
# MAGIC   GRANT ALL ON TABLES TO "<SP_CLIENT_ID>";
# MAGIC ```
# MAGIC
# MAGIC Both steps can be run from the **Lakebase SQL Editor**, **this notebook** (code cell below),
# MAGIC or any PostgreSQL client connected to the instance.
# MAGIC
# MAGIC > **Troubleshooting:** If the app shows "password authentication failed" and the
# MAGIC > Lakebase Roles UI shows **"No login"** for the SP, the OAuth role was not created
# MAGIC > properly. Run `SELECT databricks_create_role('<SP_CLIENT_ID>', 'service_principal');`
# MAGIC > to fix it.
# MAGIC
# MAGIC See `docs/PERMISSIONS.md` for the full permission model.

# COMMAND ----------

# MAGIC %pip install "databricks-sdk>=0.81.0" "psycopg[binary]>=3.0" --quiet
# MAGIC dbutils.library.restartPython()

# COMMAND ----------

# MAGIC %run ../../_setup

# COMMAND ----------

# MAGIC %md
# MAGIC ### Look up the SP client ID

# COMMAND ----------

APP_NAME = "lakebase-lab-console"

app = w.apps.get(name=APP_NAME)
sp = w.service_principals.get(id=app.service_principal_id)
SP_CLIENT_ID = sp.application_id

print(f"App:          {APP_NAME}")
print(f"SP Name:      {sp.display_name}")
print(f"SP Client ID: {SP_CLIENT_ID}")

# COMMAND ----------

# MAGIC %md
# MAGIC ### Create OAuth role and grant permissions

# COMMAND ----------

conn = get_connection()

with conn.cursor() as cur:
    cur.execute("CREATE EXTENSION IF NOT EXISTS databricks_auth")
    cur.execute(f"SELECT databricks_create_role('{SP_CLIENT_ID}', 'service_principal')")
    cur.execute(f'GRANT ALL ON SCHEMA demo TO "{SP_CLIENT_ID}"')
    cur.execute(f'GRANT ALL ON ALL TABLES IN SCHEMA demo TO "{SP_CLIENT_ID}"')
    cur.execute(f'GRANT ALL ON ALL SEQUENCES IN SCHEMA demo TO "{SP_CLIENT_ID}"')
    cur.execute(f'ALTER DEFAULT PRIVILEGES IN SCHEMA demo GRANT ALL ON TABLES TO "{SP_CLIENT_ID}"')
conn.commit()
conn.close()

print(f"✓ Created OAuth role and granted schema permissions on demo to SP: {SP_CLIENT_ID}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Verify
# MAGIC
# MAGIC Once the app is running, open it from **Workspace → Apps** and check
# MAGIC the health endpoint:
# MAGIC
# MAGIC ```
# MAGIC https://<your-app-url>/health
# MAGIC ```
# MAGIC
# MAGIC You should see `{"status": "healthy"}`.

# COMMAND ----------

# MAGIC %md
# MAGIC ---
# MAGIC ## Workshop Complete!
# MAGIC
# MAGIC You've deployed a full-stack app backed by Lakebase. Here's a summary of every lab path in the workshop:
# MAGIC
# MAGIC | Path | Lab Folder | Feature |
# MAGIC |------|-----------|---------|
# MAGIC | **Foundation** | `notebooks/` | Project setup, architecture, schema seeding |
# MAGIC | **Data Operations** | `labs/data-operations/` | CRUD, JSONB, arrays, audit triggers, transactions |
# MAGIC | **Reverse ETL** | `labs/reverse-etl/` | Sync Delta Lake tables into Lakebase |
# MAGIC | **Development Experience** | `labs/development-experience/` | Git-like branching, autoscaling, scale-to-zero |
# MAGIC | **Observability** | `labs/observability/` | pg_stat views, index analysis, monitoring |
# MAGIC | **Authentication** | `labs/authentication/` | OAuth tokens, roles, two-layer permissions |
# MAGIC | **Backup & Recovery** | `labs/backup-recovery/` | PITR, branch snapshots, instant restore |
# MAGIC | **Agentic Memory** | `labs/agentic-memory/` | Persistent AI agent memory with sessions |
# MAGIC | **Online Feature Store** | `labs/online-feature-store/` | Real-time ML feature serving |
# MAGIC | **App Deployment** | `labs/app-deployment/` | Full-stack React + FastAPI app (this lab) |
# MAGIC
# MAGIC Explore any paths you haven't tried yet — each one is independent and self-contained.
