# Databricks notebook source
# MAGIC %md
# MAGIC # Backup & Recovery
# MAGIC
# MAGIC **Path:** Backup & Recovery &nbsp;|&nbsp; **Prerequisite:** `00_Setup_Lakebase_Project`
# MAGIC
# MAGIC **Lakebase features:** Point-in-time recovery (PITR), branch snapshots, instant restore
# MAGIC
# MAGIC In this notebook you will:
# MAGIC 1. Understand Lakebase's built-in backup architecture
# MAGIC 2. Create a "snapshot" branch to preserve a known-good state
# MAGIC 3. Simulate a data loss scenario on a development branch
# MAGIC 4. Recover the data by creating a new branch from the snapshot
# MAGIC 5. Learn about point-in-time recovery (PITR) via the SDK
# MAGIC
# MAGIC **Run `00_Setup_Lakebase_Project` first.**

# COMMAND ----------

# MAGIC %pip install "databricks-sdk>=0.81.0" "psycopg[binary]>=3.0" --quiet
# MAGIC dbutils.library.restartPython()

# COMMAND ----------

# MAGIC %run ../_setup

# COMMAND ----------

import time
from databricks.sdk.service.postgres import Branch, BranchSpec, Duration

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Lakebase Backup Architecture
# MAGIC
# MAGIC Lakebase provides **multiple layers of data protection** built in:
# MAGIC
# MAGIC | Feature | How It Works | Use Case |
# MAGIC |---------|-------------|----------|
# MAGIC | **Continuous WAL archival** | Write-ahead logs are continuously streamed to durable storage | Foundation for PITR |
# MAGIC | **Point-in-Time Recovery** | Restore to any second within the configured window (up to 35 days) | Accidental data corruption or deletion |
# MAGIC | **Branch snapshots** | Create a copy-on-write branch as a named checkpoint | Pre-migration safety net |
# MAGIC | **Branch TTL** | Branches auto-delete after a configurable time | Dev/test cleanup |
# MAGIC
# MAGIC **You do NOT need to configure backups.** They are always on. The recovery
# MAGIC window is configured at the project level.

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Create a Snapshot Branch
# MAGIC
# MAGIC Before making risky changes (schema migration, bulk delete, etc.),
# MAGIC create a branch as a **named checkpoint**. This is instant and
# MAGIC costs no additional storage until data diverges.

# COMMAND ----------

SNAPSHOT_BRANCH = "lab-snapshot-pre-migration"

try:
    result = w.postgres.create_branch(
        parent=f"projects/{PROJECT_ID}",
        branch=Branch(
            spec=BranchSpec(
                source_branch=f"projects/{PROJECT_ID}/branches/production",
                ttl=Duration(seconds=172800),  # 48 hours
            )
        ),
        branch_id=SNAPSHOT_BRANCH,
    ).wait()
    print(f"✓ Snapshot branch created: {result.name}")
except Exception as e:
    if "already exists" in str(e).lower():
        print(f"Snapshot branch {SNAPSHOT_BRANCH} already exists — continuing")
    else:
        raise

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Simulate a Risky Change
# MAGIC
# MAGIC Let's create a working branch, make changes, and then simulate
# MAGIC a "bad migration" that destroys data.

# COMMAND ----------

WORK_BRANCH = "lab-migration-test"

try:
    result = w.postgres.create_branch(
        parent=f"projects/{PROJECT_ID}",
        branch=Branch(
            spec=BranchSpec(
                source_branch=f"projects/{PROJECT_ID}/branches/production",
                ttl=Duration(seconds=86400),
            )
        ),
        branch_id=WORK_BRANCH,
    ).wait()
    print(f"✓ Work branch created: {result.name}")
except Exception as e:
    if "already exists" in str(e).lower():
        print(f"Work branch {WORK_BRANCH} already exists — continuing")
    else:
        raise

# COMMAND ----------

print("Waiting for work branch endpoint...")
time.sleep(10)
work_conn = get_connection(WORK_BRANCH)
print("✓ Connected to work branch")

# COMMAND ----------

# MAGIC %md
# MAGIC ### Check current state (before the "bad migration")

# COMMAND ----------

with work_conn.cursor() as cur:
    cur.execute("SELECT count(*) AS cnt FROM demo.products")
    print(f"Products before migration: {cur.fetchone()['cnt']}")

# COMMAND ----------

# MAGIC %md
# MAGIC ### Simulate the disaster — accidentally drop the products table

# COMMAND ----------

with work_conn.cursor() as cur:
    cur.execute("DROP TABLE IF EXISTS demo.products CASCADE")
work_conn.commit()
print("💥 Products table dropped! (simulated bad migration)")

with work_conn.cursor() as cur:
    try:
        cur.execute("SELECT count(*) FROM demo.products")
    except Exception as e:
        print(f"Confirmed: {e}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Recover from the Snapshot
# MAGIC
# MAGIC The production branch is untouched (we did the damage on a work branch).
# MAGIC But if this *had* been production, here's how you'd recover:
# MAGIC
# MAGIC **Option A: Create a new branch from the snapshot**

# COMMAND ----------

RECOVERY_BRANCH = "lab-recovered"

try:
    result = w.postgres.create_branch(
        parent=f"projects/{PROJECT_ID}",
        branch=Branch(
            spec=BranchSpec(
                source_branch=f"projects/{PROJECT_ID}/branches/{SNAPSHOT_BRANCH}",
                ttl=Duration(seconds=86400),
            )
        ),
        branch_id=RECOVERY_BRANCH,
    ).wait()
    print(f"✓ Recovery branch created from snapshot: {result.name}")
except Exception as e:
    if "already exists" in str(e).lower():
        print(f"Recovery branch {RECOVERY_BRANCH} already exists — continuing")
    else:
        raise

# COMMAND ----------

print("Waiting for recovery branch endpoint...")
time.sleep(10)
recovery_conn = get_connection(RECOVERY_BRANCH)

with recovery_conn.cursor() as cur:
    cur.execute("SELECT count(*) AS cnt FROM demo.products")
    count = cur.fetchone()['cnt']
    print(f"✓ Products on recovered branch: {count}")
    print("  Data is fully intact — recovered from snapshot!")

recovery_conn.close()

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5. Point-in-Time Recovery (PITR)
# MAGIC
# MAGIC For production scenarios where you need to recover to an *exact moment*
# MAGIC (not just a named snapshot), Lakebase supports PITR.
# MAGIC
# MAGIC ### How PITR Works
# MAGIC
# MAGIC 1. Lakebase continuously archives WAL (write-ahead log) segments
# MAGIC 2. You specify a target timestamp
# MAGIC 3. A new branch is created by replaying WAL up to that timestamp
# MAGIC 4. The recovered branch is a full, independent copy of the database
# MAGIC
# MAGIC ### Using PITR via the SDK
# MAGIC
# MAGIC ```python
# MAGIC from datetime import datetime, timezone, timedelta
# MAGIC from databricks.sdk.service.postgres import Branch, BranchSpec
# MAGIC from google.protobuf.timestamp_pb2 import Timestamp
# MAGIC
# MAGIC # Recover to 30 minutes ago
# MAGIC target = datetime.now(timezone.utc) - timedelta(minutes=30)
# MAGIC
# MAGIC ts = Timestamp()
# MAGIC ts.FromDatetime(target)
# MAGIC
# MAGIC w.postgres.create_branch(
# MAGIC     parent=f"projects/{PROJECT_ID}",
# MAGIC     branch=Branch(
# MAGIC         spec=BranchSpec(
# MAGIC             source_branch=f"projects/{PROJECT_ID}/branches/production",
# MAGIC             parent_timestamp=ts,
# MAGIC         )
# MAGIC     ),
# MAGIC     branch_id="pitr-recovery",
# MAGIC ).wait()
# MAGIC ```
# MAGIC
# MAGIC ### Recovery Window
# MAGIC
# MAGIC - Default: **7 days**
# MAGIC - Maximum: **35 days**
# MAGIC - Configurable at the project level
# MAGIC - You can recover to any **second** within the window

# COMMAND ----------

# MAGIC %md
# MAGIC ## 6. Best Practices
# MAGIC
# MAGIC | Scenario | Recommended Approach |
# MAGIC |----------|---------------------|
# MAGIC | **Before a schema migration** | Create a snapshot branch (instant, free until divergence) |
# MAGIC | **Accidental DELETE/UPDATE** | PITR to the second before the mistake |
# MAGIC | **Testing destructive operations** | Create a work branch, test there, delete when done |
# MAGIC | **Compliance / audit retention** | Set PITR window to 35 days at the project level |
# MAGIC | **Disaster recovery drill** | Periodically create a branch from PITR, verify data integrity |

# COMMAND ----------

# MAGIC %md
# MAGIC ## 7. Clean Up (Optional)
# MAGIC
# MAGIC Delete the branches created in this notebook. Production is untouched.

# COMMAND ----------

# UNCOMMENT TO CLEAN UP:
# work_conn.close()
# for branch in [WORK_BRANCH, SNAPSHOT_BRANCH, RECOVERY_BRANCH]:
#     try:
#         w.postgres.delete_branch(name=f"projects/{PROJECT_ID}/branches/{branch}").wait()
#         print(f"✓ Deleted {branch}")
#     except Exception as e:
#         print(f"  {branch}: {e}")

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
# MAGIC | **Agentic Memory** | `labs/agentic-memory/` | Persistent AI agent memory with session/message storage |
# MAGIC | **App Deployment** | `labs/app-deployment/` | Full-stack React + FastAPI app using Lakebase (capstone) |
