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

# MAGIC %pip install "databricks-sdk>=0.81.0" "psycopg[binary]>=3.0" --quiet
# MAGIC dbutils.library.restartPython()

# COMMAND ----------

# MAGIC %run ../../_setup

# COMMAND ----------

# MAGIC %md
# MAGIC ## Configuration
# MAGIC
# MAGIC Set your catalog and schema below. The lab will create the schema if it
# MAGIC doesn't exist. By default it generates a sample `sample_products` table —
# MAGIC set `USE_OWN_DATA = True` if you want to sync an existing Delta table instead.

# COMMAND ----------

UC_CATALOG = "main"  # point to your own catalog
UC_SCHEMA  = f"lakebase_lab_{_sanitize(user_email).replace('-', '_')}"

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
# MAGIC
# MAGIC **Using your own data?** Update `PRIMARY_KEY_COLUMNS` below to match
# MAGIC your table's primary key.

# COMMAND ----------

from databricks.sdk.service.postgres import (
    SyncedTable,
    SyncedTableSyncedTableSpec,
    SyncedTableSyncedTableSpecSyncedTableSchedulingPolicy,
    NewPipelineSpec,
)

PRIMARY_KEY_COLUMNS = ["product_id"]

synced_table = w.postgres.create_synced_table(
    synced_table=SyncedTable(
        spec=SyncedTableSyncedTableSpec(
            branch=f"projects/{PROJECT_ID}/branches/production",
            postgres_database="databricks_postgres",
            source_table_full_name=SOURCE_TABLE,
            primary_key_columns=PRIMARY_KEY_COLUMNS,
            scheduling_policy=SyncedTableSyncedTableSpecSyncedTableSchedulingPolicy.TRIGGERED,
            new_pipeline_spec=NewPipelineSpec(
                storage_catalog=UC_CATALOG,
                storage_schema=UC_SCHEMA,
            ),
        ),
    ),
    synced_table_id=SYNCED_TABLE,
)
print(f"✓ Synced table created: {SYNCED_TABLE}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Check Sync Status

# COMMAND ----------

status = w.postgres.get_synced_table(name=f"synced_tables/{SYNCED_TABLE}")
print(f"State:   {status.status.detailed_state}")
print(f"Message: {status.status.message or 'N/A'}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Update Source & Trigger Re-sync
# MAGIC Add rows to the Delta table, then trigger the pipeline again to see
# MAGIC Reverse ETL push the changes to Lakebase.
# MAGIC
# MAGIC **Using your own data?** Make a change to your source table (insert, update,
# MAGIC or delete), then trigger a sync from Catalog Explorer → Synced Tables tab.

# COMMAND ----------

if not USE_OWN_DATA:
    spark.sql(f"""
    INSERT INTO {SOURCE_TABLE} VALUES
        (6, 'Standing Desk', 299.99, 'Office', current_timestamp()),
        (7, 'Monitor Arm', 89.99, 'Accessories', current_timestamp())
    """)
    print("✓ New rows added to sample table.")
else:
    print("Make a change to your source table, then trigger a re-sync.")

print("Trigger a sync from Catalog Explorer → Synced Tables tab, or wait for the scheduled run.")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5. Grant Service Principal Access (for App)
# MAGIC
# MAGIC If you plan to deploy the Lab Console app, its Service Principal needs
# MAGIC explicit access to synced tables. Connect to Lakebase with `psql` or
# MAGIC the Authentication lab and run:
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
# MAGIC | **Data Operations** | `labs/application-development/data-operations/` | CRUD, JSONB queries, array operators, audit triggers, transactions |
# MAGIC | **Development Experience** | `labs/platform-administration/development-experience/` | Git-like branching, autoscaling compute, scale-to-zero |
# MAGIC | **Observability** | `labs/data-integration/observability/` | pg_stat views, index analysis, connection monitoring |
# MAGIC | **Authentication** | `labs/platform-administration/authentication/` | OAuth tokens, two-layer permissions, role grants |
# MAGIC | **Backup & Recovery** | `labs/platform-administration/backup-recovery/` | Point-in-time recovery, branch snapshots, instant restore |
# MAGIC | **Agentic Memory** | `labs/application-development/agentic-memory/` | Persistent AI agent memory with session/message storage |
# MAGIC | **Online Feature Store** | `labs/data-integration/online-feature-store/` | Real-time ML feature serving powered by Lakebase Autoscaling |
# MAGIC | **App Deployment** | `labs/application-development/app-deployment/` | Full-stack React + FastAPI app using Lakebase (capstone) |
