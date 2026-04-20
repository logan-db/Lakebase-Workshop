# Databricks notebook source
# MAGIC %md
# MAGIC # Reverse ETL: Create a Synced Table
# MAGIC
# MAGIC This lab creates a Delta table in Unity Catalog and syncs it to your
# MAGIC Lakebase project using Reverse ETL (synced tables).
# MAGIC
# MAGIC **Prerequisites:**
# MAGIC - A running Lakebase Autoscaling project (from the bootstrap step)
# MAGIC - A Unity Catalog catalog and schema you can write to
# MAGIC
# MAGIC **What this demonstrates:**
# MAGIC - Creating a Delta table with Change Data Feed enabled
# MAGIC - Setting up a synced table to push data to Lakebase
# MAGIC - Checking sync status

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 1: Configuration
# MAGIC Update these values for your environment.

# COMMAND ----------

# Replace with your values
UC_CATALOG = "<your-catalog>"
UC_SCHEMA = "<your-schema>"
LAKEBASE_PROJECT_ID = "<your-project-id>"

SOURCE_TABLE = f"{UC_CATALOG}.{UC_SCHEMA}.sample_products"
SYNCED_TABLE_NAME = f"{UC_CATALOG}.{UC_SCHEMA}.products_synced"

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 2: Create a Delta Source Table

# COMMAND ----------

spark.sql(f"CREATE SCHEMA IF NOT EXISTS {UC_CATALOG}.{UC_SCHEMA}")

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

display(spark.sql(f"SELECT * FROM {SOURCE_TABLE}"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 3: Create the Synced Table

# COMMAND ----------

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.database import (
    SyncedDatabaseTable,
    SyncedTableSpec,
    NewPipelineSpec,
    SyncedTableSchedulingPolicy,
)

w = WorkspaceClient()

synced_table = w.database.create_synced_database_table(
    SyncedDatabaseTable(
        name=SYNCED_TABLE_NAME,
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

print(f"Synced table created: {synced_table.name}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 4: Check Sync Status

# COMMAND ----------

status = w.database.get_synced_database_table(name=SYNCED_TABLE_NAME)
print(f"State: {status.data_synchronization_status.detailed_state}")
print(f"Message: {status.data_synchronization_status.message}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 5: Grant SP Access to the Synced Table
# MAGIC
# MAGIC After the sync completes, grant the App's Service Principal access
# MAGIC to the new table. Synced tables are owned by the sync pipeline,
# MAGIC not your user, so `ALTER DEFAULT PRIVILEGES` does not cover them.
# MAGIC
# MAGIC ```sql
# MAGIC -- Run this against your Lakebase endpoint:
# MAGIC GRANT ALL ON ALL TABLES IN SCHEMA demo TO "<SP_CLIENT_ID>";
# MAGIC ```

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 6: Update the Source and Trigger Re-sync
# MAGIC
# MAGIC Add new rows to the Delta table and trigger a re-sync to see
# MAGIC Reverse ETL in action.

# COMMAND ----------

spark.sql(f"""
INSERT INTO {SOURCE_TABLE} VALUES
    (6, 'Standing Desk', 299.99, 'Office', current_timestamp()),
    (7, 'Monitor Arm', 89.99, 'Accessories', current_timestamp())
""")

print("New rows added. Trigger a sync from the Catalog Explorer or via SDK.")
