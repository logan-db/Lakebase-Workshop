# Databricks notebook source
# MAGIC %md
# MAGIC # Online Feature Store with Lakebase
# MAGIC
# MAGIC **Path:** Online Feature Store &nbsp;|&nbsp; **Prerequisite:** `00_Setup_Lakebase_Project`
# MAGIC
# MAGIC **Lakebase feature:** Real-time feature serving powered by Lakebase Autoscaling
# MAGIC
# MAGIC In this notebook you will:
# MAGIC 1. Create a feature table in Unity Catalog
# MAGIC 2. Provision an online feature store (backed by Lakebase Autoscaling)
# MAGIC 3. Publish features for low-latency serving
# MAGIC 4. Explore online features through the Lakebase PostgreSQL interface
# MAGIC 5. Clean up resources
# MAGIC
# MAGIC **Requirements:**
# MAGIC - Run `00_Setup_Lakebase_Project` first
# MAGIC - **DBR 16.4 LTS ML** or **serverless** compute
# MAGIC - A Unity Catalog catalog & schema with write access
# MAGIC
# MAGIC > **Why Lakebase?** Databricks Online Feature Stores are backed by Lakebase
# MAGIC > Autoscaling — the same managed PostgreSQL you explored in other labs. This
# MAGIC > means your online features get automatic scaling, low-latency reads, and
# MAGIC > direct PostgreSQL access out of the box.

# COMMAND ----------

# MAGIC %pip install "databricks-sdk>=0.81.0" "databricks-feature-engineering>=0.13.0" "psycopg[binary]>=3.0" --quiet

# COMMAND ----------

dbutils.library.restartPython()

# COMMAND ----------

# MAGIC %run ../_setup

# COMMAND ----------

from databricks.feature_engineering import FeatureEngineeringClient

fe = FeatureEngineeringClient()
print(f"✓ Feature Engineering client initialized")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Configuration
# MAGIC
# MAGIC Set your catalog and schema below. The online store name is scoped to your
# MAGIC user — each participant gets their own Lakebase Autoscaling instance.

# COMMAND ----------

UC_CATALOG = "main"
UC_SCHEMA = f"lakebase_lab_{_sanitize(user_email).replace('-', '_')}"

FEATURE_TABLE = f"{UC_CATALOG}.{UC_SCHEMA}.customer_features"
ONLINE_TABLE = f"{UC_CATALOG}.{UC_SCHEMA}.customer_features_online"
ONLINE_STORE_NAME = f"feature-store-{_sanitize(user_email)}"

print(f"Catalog:       {UC_CATALOG}")
print(f"Schema:        {UC_SCHEMA}")
print(f"Feature table: {FEATURE_TABLE}")
print(f"Online table:  {ONLINE_TABLE}")
print(f"Online store:  {ONLINE_STORE_NAME}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Create the Offline Feature Table
# MAGIC
# MAGIC The offline feature table lives in Unity Catalog as a regular Delta table.
# MAGIC Before it can be published to an online store, it needs:
# MAGIC - A **primary key** constraint (non-nullable)
# MAGIC - **Change Data Feed** enabled (for incremental sync)
# MAGIC
# MAGIC We'll use the Feature Engineering client to create the table with the proper
# MAGIC primary key, then enable CDF separately.

# COMMAND ----------

spark.sql(f"CREATE SCHEMA IF NOT EXISTS {UC_CATALOG}.{UC_SCHEMA}")

from pyspark.sql.types import (
    StructType, StructField, IntegerType, DoubleType, StringType, DateType,
)
from datetime import date

schema = StructType([
    StructField("customer_id", IntegerType(), nullable=False),
    StructField("total_orders", IntegerType()),
    StructField("avg_order_value", DoubleType()),
    StructField("preferred_category", StringType()),
    StructField("lifetime_value", DoubleType()),
    StructField("risk_score", DoubleType()),
    StructField("last_order_date", DateType()),
])

data = [
    (1001, 47, 156.80, "Electronics", 7432.60, 0.12, date(2026, 4, 20)),
    (1002, 12, 89.50, "Books",       1074.00, 0.45, date(2026, 4, 18)),
    (1003, 95, 210.25, "Electronics", 19973.75, 0.05, date(2026, 4, 21)),
    (1004, 3,  42.99, "Office",       128.97, 0.78, date(2026, 4, 10)),
    (1005, 28, 175.40, "Accessories", 4911.20, 0.22, date(2026, 4, 19)),
    (1006, 61, 134.60, "Electronics", 8210.60, 0.08, date(2026, 4, 21)),
    (1007, 8,  55.75, "Books",        446.00, 0.62, date(2026, 4, 15)),
    (1008, 34, 198.90, "Electronics", 6762.60, 0.15, date(2026, 4, 20)),
    (1009, 19, 112.30, "Accessories", 2133.70, 0.31, date(2026, 4, 17)),
    (1010, 72, 88.45, "Office",       6368.40, 0.09, date(2026, 4, 21)),
]

features_df = spark.createDataFrame(data, schema=schema)

if spark.catalog.tableExists(FEATURE_TABLE):
    print(f"Feature table already exists: {FEATURE_TABLE}")
else:
    fe.create_table(
        name=FEATURE_TABLE,
        primary_keys=["customer_id"],
        df=features_df,
        description="Customer features for real-time personalization and fraud detection",
    )
    print(f"✓ Feature table created: {FEATURE_TABLE}")

# COMMAND ----------

spark.sql(f"""
ALTER TABLE {FEATURE_TABLE}
SET TBLPROPERTIES ('delta.enableChangeDataFeed' = 'true')
""")
print(f"✓ Change Data Feed enabled on {FEATURE_TABLE}")

display(spark.sql(f"SELECT * FROM {FEATURE_TABLE} ORDER BY customer_id"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Create an Online Feature Store
# MAGIC
# MAGIC The `create_online_store` API provisions a **Lakebase Autoscaling** instance
# MAGIC dedicated to serving features at low latency. This is the same managed
# MAGIC PostgreSQL service you used in the other workshop labs — but created and
# MAGIC managed through the Feature Engineering client.
# MAGIC
# MAGIC | Capacity | CU Range | Use Case |
# MAGIC |----------|----------|----------|
# MAGIC | CU_1 | Smallest | Dev/test, small feature sets |
# MAGIC | CU_2 | Medium | Production, moderate traffic |
# MAGIC | CU_4 | Large | High throughput |
# MAGIC | CU_8 | Largest | Very high concurrency |

# COMMAND ----------

try:
    existing = fe.get_online_store(name=ONLINE_STORE_NAME)
    print(f"Online store already exists: {ONLINE_STORE_NAME} (state: {existing.state})")
except Exception:
    fe.create_online_store(
        name=ONLINE_STORE_NAME,
        capacity="CU_1",
    )
    print(f"✓ Online store creation initiated: {ONLINE_STORE_NAME}")
    print("  This provisions a Lakebase Autoscaling instance (takes 2–4 minutes)...")

# COMMAND ----------

import time

TIMEOUT_MINUTES = 15
print(f"Waiting for online store '{ONLINE_STORE_NAME}' to become available (timeout: {TIMEOUT_MINUTES} min)...")
deadline = time.monotonic() + TIMEOUT_MINUTES * 60

while True:
    store = fe.get_online_store(name=ONLINE_STORE_NAME)
    state_str = str(store.state).upper()
    print(f"  State: {store.state}  (raw: {state_str})")

    if "AVAILABLE" in state_str or "ACTIVE" in state_str:
        break
    if any(s in state_str for s in ("FAILED", "DELETED", "ERROR")):
        raise RuntimeError(f"Online store failed with state: {store.state}")
    if time.monotonic() > deadline:
        raise TimeoutError(
            f"Online store did not become available within {TIMEOUT_MINUTES} minutes. "
            f"Last state: {store.state}. Check the Lakebase UI."
        )
    time.sleep(15)

print(f"\n✓ Online store is ready!")
print(f"  Name:     {store.name}")
print(f"  State:    {store.state}")
print(f"  Capacity: {store.capacity}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Publish Features to Online Store
# MAGIC
# MAGIC Publishing syncs your offline feature table into the online store for
# MAGIC low-latency reads. The default **TRIGGERED** mode does a one-time sync —
# MAGIC you can re-run `publish_table` to push updates, or switch to **CONTINUOUS**
# MAGIC mode for streaming sync.
# MAGIC
# MAGIC | Publish Mode | Behavior |
# MAGIC |-------------|----------|
# MAGIC | TRIGGERED | Incremental sync on each `publish_table` call (default) |
# MAGIC | CONTINUOUS | Streaming pipeline — updates immediately as source changes |
# MAGIC | SNAPSHOT | Full copy — best when most rows change between syncs |

# COMMAND ----------

online_store = fe.get_online_store(name=ONLINE_STORE_NAME)

fe.publish_table(
    online_store=online_store,
    source_table_name=FEATURE_TABLE,
    online_table_name=ONLINE_TABLE,
)

print(f"✓ Feature table published to online store")
print(f"  Source table:  {FEATURE_TABLE}")
print(f"  Online table:  {ONLINE_TABLE}")
print(f"  Online store:  {ONLINE_STORE_NAME}")
print(f"  Publish mode:  TRIGGERED (default)")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Verify Online Features
# MAGIC
# MAGIC List all online stores accessible to you and verify the publish completed.

# COMMAND ----------

stores = fe.list_online_stores()
print("Accessible online stores:")
for s in stores:
    print(f"  {s.name} | State: {s.state} | Capacity: {s.capacity}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5. Explore Online Features via Lakebase
# MAGIC
# MAGIC Since the online store IS a Lakebase Autoscaling instance, you can connect
# MAGIC directly with standard PostgreSQL tools. This is the same `psycopg` +
# MAGIC `w.postgres` pattern you used in the other workshop labs.
# MAGIC
# MAGIC > **Note:** If the publish pipeline is still running, the feature table may
# MAGIC > not appear yet. Wait a minute and re-run this section.

# COMMAND ----------

try:
    endpoints = list(w.postgres.list_endpoints(
        parent=f"projects/{ONLINE_STORE_NAME}/branches/production"
    ))
    if not endpoints:
        print("⏳ No endpoints found yet — the online store may still be initializing.")
        print("   Wait a minute and re-run this cell.")
    else:
        ep = w.postgres.get_endpoint(name=endpoints[0].name)
        host = ep.status.hosts.host
        cred = w.postgres.generate_database_credential(endpoint=endpoints[0].name)

        import psycopg
        from psycopg.rows import dict_row

        fs_conn = psycopg.connect(
            host=host, dbname="databricks_postgres",
            user=user_email, password=cred.token,
            sslmode="require", row_factory=dict_row,
        )
        print(f"✓ Connected directly to online store: {host}")

        with fs_conn.cursor() as cur:
            cur.execute("""
                SELECT schemaname, tablename
                FROM pg_tables
                WHERE schemaname NOT IN ('pg_catalog', 'information_schema', 'pg_internal')
                ORDER BY schemaname, tablename
            """)
            tables = cur.fetchall()
            print(f"\nTables in the online store ({len(tables)} found):")
            for row in tables:
                print(f"  {row['schemaname']}.{row['tablename']}")

        fs_conn.close()
        print("\n✓ Connection closed")

except Exception as e:
    print(f"Could not connect to online store Lakebase instance: {e}")
    print("\nThis can happen if the publish pipeline is still running.")
    print("You can also query online features through the SQL editor in the")
    print("Databricks workspace UI — navigate to the online store in Catalog Explorer.")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 6. Update Features and Re-publish
# MAGIC
# MAGIC In a real workflow, features are updated by your batch or streaming pipelines.
# MAGIC Here we simulate adding new customers and re-publishing.

# COMMAND ----------

from datetime import date

new_customers = spark.createDataFrame([
    (1011, 5,  67.20, "Books",       336.00, 0.55, date(2026, 4, 22)),
    (1012, 41, 145.90, "Electronics", 5981.90, 0.10, date(2026, 4, 22)),
], schema=schema)

new_customers.write.format("delta").mode("append").saveAsTable(FEATURE_TABLE)
print(f"✓ Added 2 new customers to {FEATURE_TABLE}")

# COMMAND ----------

online_store = fe.get_online_store(name=ONLINE_STORE_NAME)
fe.publish_table(
    online_store=online_store,
    source_table_name=FEATURE_TABLE,
    online_table_name=ONLINE_TABLE,
)
print("✓ Re-published with updated features")
print("  The TRIGGERED mode incrementally syncs only the new/changed rows.")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 7. Feature Serving Endpoints
# MAGIC
# MAGIC To serve features to real-time applications (recommendation engines, fraud
# MAGIC detection, personalization), create a **Feature Serving endpoint**. The
# MAGIC endpoint handles feature lookups against the online store automatically.
# MAGIC
# MAGIC ```python
# MAGIC # Example — create a feature serving endpoint
# MAGIC from databricks.feature_engineering import FeatureEngineeringClient, FeatureLookup
# MAGIC
# MAGIC fe = FeatureEngineeringClient()
# MAGIC
# MAGIC # Define which features to serve
# MAGIC feature_lookups = [
# MAGIC     FeatureLookup(
# MAGIC         table_name="catalog.schema.customer_features",
# MAGIC         lookup_key=["customer_id"],
# MAGIC     )
# MAGIC ]
# MAGIC
# MAGIC # Models trained with feature lookups automatically resolve to online stores
# MAGIC # when deployed as serving endpoints
# MAGIC ```
# MAGIC
# MAGIC For the full walkthrough, see the
# MAGIC [Feature Serving documentation](https://docs.databricks.com/aws/en/machine-learning/feature-store/feature-serving-endpoints).

# COMMAND ----------

# MAGIC %md
# MAGIC ## Cleanup
# MAGIC
# MAGIC **Important:** Online stores continuously incur costs. Delete them when not
# MAGIC in use. Uncomment the cells below to clean up.
# MAGIC
# MAGIC ⚠️ You **must** use `delete_online_table` from the SDK — do not use
# MAGIC `DROP TABLE` in SQL, as that leaves orphaned data in the Lakebase instance.

# COMMAND ----------

# UNCOMMENT TO DELETE THE ONLINE TABLE:
# w.online_tables.delete(name=ONLINE_TABLE)
# print(f"✓ Deleted online table: {ONLINE_TABLE}")

# COMMAND ----------

# UNCOMMENT TO DELETE THE ONLINE STORE (Lakebase instance):
# fe.delete_online_store(name=ONLINE_STORE_NAME)
# print(f"✓ Deleted online store: {ONLINE_STORE_NAME}")

# COMMAND ----------

# UNCOMMENT TO DROP THE SOURCE FEATURE TABLE AND SCHEMA:
# spark.sql(f"DROP TABLE IF EXISTS {FEATURE_TABLE}")
# spark.sql(f"DROP SCHEMA IF EXISTS {UC_CATALOG}.{UC_SCHEMA} CASCADE")
# print(f"✓ Dropped {FEATURE_TABLE} and schema {UC_SCHEMA}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## What's Next?
# MAGIC
# MAGIC Continue to another lab path:
# MAGIC
# MAGIC | Path | Folder | What You'll Learn |
# MAGIC |------|--------|-------------------|
# MAGIC | **Data Operations** | `labs/data-operations/` | CRUD, JSONB queries, array operators, audit triggers, transactions |
# MAGIC | **Reverse ETL** | `labs/reverse-etl/` | Sync Delta Lake tables into Lakebase for low-latency serving |
# MAGIC | **Development Experience** | `labs/development-experience/` | Git-like branching, autoscaling compute, scale-to-zero |
# MAGIC | **Observability** | `labs/observability/` | pg_stat views, index analysis, connection monitoring |
# MAGIC | **Authentication** | `labs/authentication/` | OAuth tokens, two-layer permissions, role grants |
# MAGIC | **Backup & Recovery** | `labs/backup-recovery/` | Point-in-time recovery, branch snapshots, instant restore |
# MAGIC | **Agentic Memory** | `labs/agentic-memory/` | Persistent AI agent memory with session/message storage |
# MAGIC | **App Deployment** | `labs/app-deployment/` | Full-stack React + FastAPI app using Lakebase (capstone) |
