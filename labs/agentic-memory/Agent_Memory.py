# Databricks notebook source
# MAGIC %md
# MAGIC # Agent Memory with Lakebase
# MAGIC
# MAGIC **Path:** Agentic Memory &nbsp;|&nbsp; **Prerequisite:** `00_Setup_Lakebase_Project`
# MAGIC
# MAGIC **Lakebase feature:** Persistent session/message storage for AI agents
# MAGIC
# MAGIC In this notebook you will:
# MAGIC 1. Create an agent session
# MAGIC 2. Store a multi-turn conversation (user ↔ assistant)
# MAGIC 3. Retrieve conversation history ordered by timestamp
# MAGIC 4. Query across sessions using JSONB metadata
# MAGIC 5. Clean up expired sessions
# MAGIC
# MAGIC **Run `00_Setup_Lakebase_Project` first** (the `agent_sessions` and
# MAGIC `agent_messages` tables are created by the seed script).

# COMMAND ----------

# MAGIC %pip install "databricks-sdk>=0.81.0" "psycopg[binary]>=3.0" --quiet
# MAGIC dbutils.library.restartPython()

# COMMAND ----------

# MAGIC %run ../_setup

# COMMAND ----------

import uuid, json

conn = get_connection()
print(f"✓ Connected to {PROJECT_ID} / production")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Create an Agent Session
# MAGIC
# MAGIC Each session stores metadata about the agent and conversation context.

# COMMAND ----------

SESSION_ID = str(uuid.uuid4())[:16]

with conn.cursor() as cur:
    cur.execute("""
        INSERT INTO demo.agent_sessions (session_id, agent_name, metadata)
        VALUES (%s, %s, %s)
        RETURNING session_id, agent_name, created_at
    """, (SESSION_ID, "workshop-assistant", json.dumps({
        "model": "databricks-meta-llama-3-3-70b-instruct",
        "temperature": 0.7,
        "user": user_email,
        "purpose": "lakebase-workshop-demo"
    })))
    session = cur.fetchone()
conn.commit()
print(f"✓ Session created: {session['session_id']}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Store a Multi-Turn Conversation

# COMMAND ----------

CONVERSATION = [
    ("system", "You are a helpful data engineering assistant for Databricks Lakebase."),
    ("user",   "What is Lakebase?"),
    ("assistant", "Lakebase is a fully managed PostgreSQL database service built into Databricks. "
                  "It provides autoscaling compute, copy-on-write branching, scale-to-zero, "
                  "and tight integration with Unity Catalog."),
    ("user",   "How does branching work?"),
    ("assistant", "Branching creates an instant, isolated copy of your database using copy-on-write "
                  "storage. No data is duplicated until you make changes on the branch. This is ideal "
                  "for dev/test environments, CI pipelines, or safe schema migrations."),
    ("user",   "Can I sync data from Delta Lake?"),
    ("assistant", "Yes! Lakebase supports Reverse ETL through synced tables. You create a Delta table "
                  "with Change Data Feed enabled, then set up a synced table that pushes changes into "
                  "your Lakebase PostgreSQL branch automatically."),
]

with conn.cursor() as cur:
    for role, content in CONVERSATION:
        cur.execute("""
            INSERT INTO demo.agent_messages (session_id, role, content, metadata)
            VALUES (%s, %s, %s, %s)
        """, (SESSION_ID, role, content, json.dumps({"notebook": "05_Agent_Memory"})))
conn.commit()
print(f"✓ Stored {len(CONVERSATION)} messages in session {SESSION_ID}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Retrieve Conversation History
# MAGIC Ordered by timestamp — exactly how an agent retrieves context.

# COMMAND ----------

with conn.cursor() as cur:
    cur.execute("""
        SELECT role, content, created_at
        FROM demo.agent_messages
        WHERE session_id = %s
        ORDER BY created_at
    """, (SESSION_ID,))
    print(f"Session {SESSION_ID} — conversation:")
    for msg in cur.fetchall():
        preview = msg["content"][:100] + "..." if len(msg["content"]) > 100 else msg["content"]
        print(f"  [{msg['role']}] {preview}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Query Across Sessions
# MAGIC Use JSONB metadata to filter sessions — for example, finding all sessions
# MAGIC that used a specific model or were created by a certain user.

# COMMAND ----------

with conn.cursor() as cur:
    cur.execute("""
        SELECT s.session_id, s.agent_name,
               s.metadata->>'model' AS model,
               s.metadata->>'user' AS owner,
               COUNT(m.message_id) AS message_count,
               s.created_at
        FROM demo.agent_sessions s
        LEFT JOIN demo.agent_messages m ON s.session_id = m.session_id
        GROUP BY s.session_id, s.agent_name, s.metadata, s.created_at
        ORDER BY s.created_at DESC
    """)
    print("All sessions:")
    for row in cur.fetchall():
        print(f"  {row['session_id']} | {row['agent_name']} | "
              f"model={row['model']} | msgs={row['message_count']}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5. Clean Up Expired Sessions
# MAGIC In a real app you'd run this periodically to purge stale sessions.
# MAGIC Messages are deleted automatically via `ON DELETE CASCADE`.

# COMMAND ----------

# UNCOMMENT TO DELETE THIS SESSION:
# with conn.cursor() as cur:
#     cur.execute("DELETE FROM demo.agent_sessions WHERE session_id = %s RETURNING session_id", (SESSION_ID,))
#     deleted = cur.fetchone()
# conn.commit()
# print(f"✓ Deleted session {deleted['session_id']} and all its messages")

# COMMAND ----------

conn.close()

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
# MAGIC | **App Deployment** | `labs/app-deployment/` | Full-stack React + FastAPI app using Lakebase (capstone) |
