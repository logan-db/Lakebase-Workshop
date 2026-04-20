# Databricks notebook source
# MAGIC %md
# MAGIC # Reverse ETL (Synced Tables)
# MAGIC
# MAGIC **Path:** Reverse ETL &nbsp;|&nbsp; **Prerequisite:** `00_Setup_Lakebase_Project`
# MAGIC
# MAGIC **Lakebase feature:** Sync Delta Lake tables into Lakebase PostgreSQL
# MAGIC
# MAGIC In this notebook you will:
# MAGIC 1. Set up a Delta source table (use your own data or generate sample data)
# MAGIC 2. Set up a synced table that pushes data to Lakebase
# MAGIC 3. Check sync status
# MAGIC 4. Update the source and observe the sync
# MAGIC
# MAGIC **Prerequisites:**
# MAGIC - Run `00_Setup_Lakebase_Project` first
# MAGIC - A Unity Catalog catalog & schema with write access
# MAGIC
# MAGIC > **Bring your own data or use ours:** This lab generates a sample products table
# MAGIC > by default. If you already have a Delta table you'd like to sync, skip the
# MAGIC > sample data step and point the configuration at your own table instead.
# MAGIC
# MAGIC > **Note:** Synced tables are owned by the sync pipeline. If you deploy the
# MAGIC > Lab Console app, you must also GRANT the app's Service Principal access
# MAGIC > to synced tables. See `docs/PERMISSIONS.md`.

# COMMAND ----------

# MAGIC %pip install "databricks-sdk>=0.81.0" --quiet
# MAGIC dbutils.library.restartPython()

# COMMAND ----------

import re
from databricks.sdk import WorkspaceClient

w = WorkspaceClient()
user_email = w.current_user.me().user_name

def sanitize(email):
    name = email.split("@")[0]
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9-]", "-", name.lower())).strip("-")

PROJECT_ID = f"lakebase-lab-{sanitize(user_email)}"
print(f"Project: {PROJECT_ID}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Configuration
# MAGIC
# MAGIC Set your catalog and schema below. The lab will create the schema if it
# MAGIC doesn't exist. By default it generates a sample `sample_products` table —
# MAGIC set `USE_OWN_DATA = True` if you want to sync an existing Delta table instead.

# COMMAND ----------

UC_CATALOG = "main"
UC_SCHEMA  = f"lakebase_lab_{sanitize(user_email)}"

USE_OWN_DATA = False

if USE_OWN_DATA:
    SOURCE_TABLE = "<catalog.schema.your_table>"   # point to your existing Delta table
else:
    SOURCE_TABLE = f"{UC_CATALOG}.{UC_SCHEMA}.sample_products"

SYNCED_TABLE = f"{UC_CATALOG}.{UC_SCHEMA}.products_synced"

print(f"Catalog:      {UC_CATALOG}")
print(f"Schema:       {UC_SCHEMA}")
print(f"Source table:  {SOURCE_TABLE}")
print(f"Synced table:  {SYNCED_TABLE}")
print(f"Using own data: {USE_OWN_DATA}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Create a Delta Source Table
# MAGIC
# MAGIC Change Data Feed (CDF) must be enabled for synced tables to track changes.
# MAGIC
# MAGIC **Using your own data?** Skip this cell — just make sure your table has CDF
# MAGIC enabled: `ALTER TABLE <table> SET TBLPROPERTIES (delta.enableChangeDataFeed = true)`

# COMMAND ----------

spark.sql(f"CREATE SCHEMA IF NOT EXISTS {UC_CATALOG}.{UC_SCHEMA}")

if not USE_OWN_DATA:
    spark.sql(f"""
    CREATE TABLE IF NOT EXISTS {SOURCE_TABLE} (
        product_id INT,
        name STRING,
        price DOUBLE,
        category STRING,
        updated_at TIMESTAMP
    )
    USING DELTA
    TBLPROPERTIES (delta.enableChangeDataFeed = true)
    """)

    spark.sql(f"""
    INSERT INTO {SOURCE_TABLE} VALUES
        (1, 'Wireless Mouse', 29.99, 'Electronics', current_timestamp()),
        (2, 'USB-C Adapter', 14.99, 'Accessories', current_timestamp()),
        (3, 'Laptop Sleeve', 24.99, 'Accessories', current_timestamp()),
        (4, 'Webcam HD', 59.99, 'Electronics', current_timestamp()),
        (5, 'Desk Lamp', 34.99, 'Office', current_timestamp())
    """)
    print(f"✓ Sample data created in {SOURCE_TABLE}")
else:
    print(f"Using existing table: {SOURCE_TABLE}")

display(spark.sql(f"SELECT * FROM {SOURCE_TABLE}"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Create the Synced Table
# MAGIC This sets up a pipeline that continuously (or on trigger) pushes Delta
# MAGIC changes into the Lakebase PostgreSQL branch.

# COMMAND ----------

from databricks.sdk.service.database import (
    SyncedDatabaseTable,
    SyncedTableSpec,
    NewPipelineSpec,
    SyncedTableSchedulingPolicy,
)

synced_table = w.database.create_synced_database_table(
    SyncedDatabaseTable(
        name=SYNCED_TABLE,
        spec=SyncedTableSpec(
            source_table_full_name=SOURCE_TABLE,
            primary_key_columns=["product_id"],
            scheduling_policy=SyncedTableSchedulingPolicy.TRIGGERED,
            new_pipeline_spec=NewPipelineSpec(
                storage_catalog=UC_CATALOG,
                storage_schema=UC_SCHEMA,
            ),
        ),
    )
)

print(f"✓ Synced table created: {synced_table.name}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Check Sync Status

# COMMAND ----------

status = w.database.get_synced_database_table(name=SYNCED_TABLE)
print(f"State:   {status.data_synchronization_status.detailed_state}")
print(f"Message: {status.data_synchronization_status.message}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Update Source & Trigger Re-sync
# MAGIC Add rows to the Delta table, then trigger the pipeline again to see
# MAGIC Reverse ETL push the changes to Lakebase.

# COMMAND ----------

spark.sql(f"""
INSERT INTO {SOURCE_TABLE} VALUES
    (6, 'Standing Desk', 299.99, 'Office', current_timestamp()),
    (7, 'Monitor Arm', 89.99, 'Accessories', current_timestamp())
""")

print("✓ New rows added. Trigger a sync from Catalog Explorer → Synced Tables tab, or wait for the scheduled run.")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5. Grant Service Principal Access (for App)
# MAGIC
# MAGIC If you plan to deploy the Lab Console app, its Service Principal needs
# MAGIC explicit access to synced tables. Connect to Lakebase with `psql` or
# MAGIC notebook `03` and run:
# MAGIC
# MAGIC ```sql
# MAGIC GRANT ALL ON ALL TABLES IN SCHEMA demo TO "<SP_CLIENT_ID>";
# MAGIC ```

# COMMAND ----------

# MAGIC %md
# MAGIC ## What's Next?
# MAGIC
# MAGIC Continue to another lab path:
# MAGIC
# MAGIC | Path | Folder | What You'll Learn |
# MAGIC |------|--------|-------------------|
# MAGIC | **Data Operations** | `labs/data-operations/` | CRUD, JSONB queries, array operators, audit triggers, transactions |
# MAGIC | **Development Experience** | `labs/development-experience/` | Git-like branching, autoscaling compute, scale-to-zero |
# MAGIC | **Observability** | `labs/observability/` | pg_stat views, index analysis, connection monitoring |
# MAGIC | **Authentication** | `labs/authentication/` | OAuth tokens, two-layer permissions, role grants |
# MAGIC | **Backup & Recovery** | `labs/backup-recovery/` | Point-in-time recovery, branch snapshots, instant restore |
# MAGIC | **Agentic Memory** | `labs/agentic-memory/` | Persistent AI agent memory with session/message storage |
# MAGIC | **App Deployment** | `labs/app-deployment/` | Full-stack React + FastAPI app using Lakebase (capstone) |
