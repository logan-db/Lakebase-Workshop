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
# MAGIC 1. **Notebook `00` was run** — your Lakebase project exists
# MAGIC 2. **The frontend is built** — `build.sh` was run locally (see below)
# MAGIC 3. **Databricks CLI** is authenticated to this workspace

# COMMAND ----------

# MAGIC %md
# MAGIC ## Option A: Deploy with a Declarative Automation Bundle
# MAGIC
# MAGIC From the **root of the cloned repo** on your laptop:
# MAGIC
# MAGIC ```bash
# MAGIC # 1. Build the React frontend
# MAGIC cd apps/lakebase-lab-console
# MAGIC bash build.sh
# MAGIC
# MAGIC # 2. Go back to the repo root (where databricks.yml lives)
# MAGIC cd ../..
# MAGIC
# MAGIC # 3. Deploy the bundle
# MAGIC databricks bundle deploy --target dev
# MAGIC
# MAGIC # 4. Open the app in the Databricks UI:
# MAGIC #    Workspace → Apps → lakebase-lab-console
# MAGIC ```

# COMMAND ----------

# MAGIC %md
# MAGIC ## Option B: Deploy from the Databricks Apps UI
# MAGIC
# MAGIC 1. Go to **Workspace → Apps → Create App**
# MAGIC 2. Name it `lakebase-lab-console`
# MAGIC 3. Under **Resources**, add your Lakebase database (the `PG*` env vars
# MAGIC    will be injected automatically)
# MAGIC 4. Set these **Environment Variables**:
# MAGIC
# MAGIC | Variable | Value |
# MAGIC |----------|-------|
# MAGIC | `LAKEBASE_PROJECT_ID` | *(output from notebook 00)* |
# MAGIC | `DATABRICKS_HOST` | *(your workspace URL)* |
# MAGIC
# MAGIC 5. Upload the `apps/lakebase-lab-console` folder as the source code
# MAGIC 6. Click **Deploy**

# COMMAND ----------

# MAGIC %md
# MAGIC ## App Configuration Reference
# MAGIC
# MAGIC The app uses `app.yaml` for its configuration:
# MAGIC
# MAGIC ```yaml
# MAGIC command:
# MAGIC   - uvicorn
# MAGIC   - app:app
# MAGIC   - --workers
# MAGIC   - "4"
# MAGIC env:
# MAGIC   - name: LAKEBASE_PROJECT_ID
# MAGIC     value: <set-after-setup>
# MAGIC   - name: DATABRICKS_HOST
# MAGIC     value: <set-after-setup>
# MAGIC resources:
# MAGIC   - name: lakebase-db
# MAGIC     type: postgres
# MAGIC ```

# COMMAND ----------

# MAGIC %md
# MAGIC ## Service Principal Permissions
# MAGIC
# MAGIC When the app deploys, Databricks creates a Service Principal (SP) to run it.
# MAGIC You must grant this SP access to your Lakebase tables.
# MAGIC
# MAGIC 1. Find the SP's `client_id` in the **App details** page
# MAGIC 2. Connect to Lakebase (e.g., using notebook `03` or psql)
# MAGIC 3. Run:
# MAGIC
# MAGIC ```sql
# MAGIC GRANT ALL ON SCHEMA demo TO "<SP_CLIENT_ID>";
# MAGIC GRANT ALL ON ALL TABLES IN SCHEMA demo TO "<SP_CLIENT_ID>";
# MAGIC GRANT ALL ON ALL SEQUENCES IN SCHEMA demo TO "<SP_CLIENT_ID>";
# MAGIC ALTER DEFAULT PRIVILEGES IN SCHEMA demo
# MAGIC   GRANT ALL ON TABLES TO "<SP_CLIENT_ID>";
# MAGIC ```
# MAGIC
# MAGIC See `docs/PERMISSIONS.md` for the full permission model.

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
# MAGIC You have explored every core Lakebase Autoscaling feature:
# MAGIC
# MAGIC | Notebook | Feature |
# MAGIC |----------|---------|
# MAGIC | **00** | Lakebase architecture, project setup & schema seeding |
# MAGIC | **01** | Copy-on-write branching |
# MAGIC | **02** | Authentication, OAuth tokens & permissions |
# MAGIC | **03** | Autoscaling compute & scale-to-zero |
# MAGIC | **04** | CRUD, JSONB, arrays, audit triggers, transactions |
# MAGIC | **05** | Database observability & monitoring |
# MAGIC | **06** | Reverse ETL with synced tables |
# MAGIC | **07** | Backup & point-in-time recovery |
# MAGIC | **08** | Agent memory (sessions + messages) |
# MAGIC | **09** | Full-stack app deployment |
# MAGIC
# MAGIC Check out the `labs/` folder for additional exercises:
# MAGIC - `labs/advanced-sql/` — advanced PostgreSQL SQL patterns
# MAGIC - `labs/reverse-etl/` — standalone synced table lab
