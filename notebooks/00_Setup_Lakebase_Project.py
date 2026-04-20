# Databricks notebook source
# MAGIC %md
# MAGIC # 00 — Set Up Your Lakebase Autoscaling Project
# MAGIC
# MAGIC This notebook creates your Lakebase Autoscaling project, waits for the
# MAGIC endpoint to become active, and seeds the demo schema with sample data.
# MAGIC
# MAGIC **Run this notebook once** before starting any of the workshop labs.
# MAGIC
# MAGIC ### What gets created
# MAGIC | Resource | Details |
# MAGIC |----------|---------|
# MAGIC | **Project** | `lakebase-lab-<your-username>` |
# MAGIC | **Branch** | `production` (auto-created, default) |
# MAGIC | **Compute** | Autoscaling endpoint (0.5+ CU) |
# MAGIC | **Schema** | `demo` with 5 tables: products, events, agent_sessions, agent_messages, audit_log |
# MAGIC | **Sample data** | 8 products with JSONB metadata, array tags, and audit triggers |

# COMMAND ----------

# MAGIC %md
# MAGIC ## Lakebase Architecture
# MAGIC
# MAGIC Lakebase Autoscaling is Databricks' fully managed **PostgreSQL 17** service
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
# MAGIC dbutils.library.restartPython()

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
PG_VERSION = "17"

print(f"User:       {user_email}")
print(f"Project ID: {PROJECT_ID}")

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
# MAGIC ## Step 4: Connect and Seed the Demo Schema
# MAGIC Creates 5 tables, indexes, audit triggers, and inserts 8 sample products.

# COMMAND ----------

import psycopg
import subprocess
import socket

host = endpoint.status.hosts.host
cred = w.postgres.generate_database_credential(endpoint=endpoint.name)
username = user_email

# macOS DNS workaround
def resolve(hostname):
    try:
        return socket.gethostbyname(hostname)
    except socket.gaierror:
        pass
    try:
        result = subprocess.run(["dig", "+short", hostname], capture_output=True, text=True, timeout=5)
        for line in result.stdout.strip().split("\n"):
            line = line.strip()
            if line and not line.startswith(";"):
                return line
    except Exception:
        pass
    return None

params = {"host": host, "dbname": "databricks_postgres", "user": username, "password": cred.token, "sslmode": "require"}
hostaddr = resolve(host)
if hostaddr:
    params["hostaddr"] = hostaddr

conn = psycopg.connect(**params)
print(f"✓ Connected to Lakebase")

# COMMAND ----------

SEED_SQL = """
CREATE SCHEMA IF NOT EXISTS demo;

CREATE TABLE IF NOT EXISTS demo.products (
    product_id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    price DECIMAL(10, 2) NOT NULL CHECK (price >= 0),
    stock_quantity INTEGER DEFAULT 0 CHECK (stock_quantity >= 0),
    category VARCHAR(100),
    tags TEXT[],
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS demo.events (
    event_id SERIAL PRIMARY KEY,
    event_type VARCHAR(50) NOT NULL,
    source VARCHAR(100),
    payload JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS demo.agent_sessions (
    session_id VARCHAR(64) PRIMARY KEY,
    agent_name VARCHAR(100) NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS demo.agent_messages (
    message_id SERIAL PRIMARY KEY,
    session_id VARCHAR(64) NOT NULL REFERENCES demo.agent_sessions(session_id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant', 'system', 'tool')),
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS demo.audit_log (
    audit_id SERIAL PRIMARY KEY,
    table_name VARCHAR(100) NOT NULL,
    operation VARCHAR(10) NOT NULL CHECK (operation IN ('INSERT', 'UPDATE', 'DELETE')),
    record_id INTEGER,
    old_data JSONB,
    new_data JSONB,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100) DEFAULT CURRENT_USER
);

CREATE INDEX IF NOT EXISTS idx_events_type ON demo.events(event_type);
CREATE INDEX IF NOT EXISTS idx_events_created ON demo.events(created_at);
CREATE INDEX IF NOT EXISTS idx_messages_session ON demo.agent_messages(session_id);
CREATE INDEX IF NOT EXISTS idx_products_category ON demo.products(category);
CREATE INDEX IF NOT EXISTS idx_products_tags ON demo.products USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_audit_table ON demo.audit_log(table_name);

CREATE OR REPLACE FUNCTION demo.audit_trigger_fn()
RETURNS TRIGGER AS $$
DECLARE
    pk_col TEXT;
    rec_id INTEGER;
BEGIN
    pk_col := CASE TG_TABLE_NAME
        WHEN 'products' THEN 'product_id'
        WHEN 'events'   THEN 'event_id'
        WHEN 'agent_messages' THEN 'message_id'
        ELSE NULL
    END;

    IF TG_OP = 'INSERT' THEN
        rec_id := (row_to_json(NEW)::jsonb ->> pk_col)::int;
        INSERT INTO demo.audit_log (table_name, operation, record_id, new_data)
        VALUES (TG_TABLE_NAME, 'INSERT', rec_id, row_to_json(NEW)::jsonb);
        RETURN NEW;
    ELSIF TG_OP = 'UPDATE' THEN
        rec_id := (row_to_json(NEW)::jsonb ->> pk_col)::int;
        INSERT INTO demo.audit_log (table_name, operation, record_id, old_data, new_data)
        VALUES (TG_TABLE_NAME, 'UPDATE', rec_id, row_to_json(OLD)::jsonb, row_to_json(NEW)::jsonb);
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        rec_id := (row_to_json(OLD)::jsonb ->> pk_col)::int;
        INSERT INTO demo.audit_log (table_name, operation, record_id, old_data)
        VALUES (TG_TABLE_NAME, 'DELETE', rec_id, row_to_json(OLD)::jsonb);
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_audit_products ON demo.products;
CREATE TRIGGER trg_audit_products
    AFTER INSERT OR UPDATE OR DELETE ON demo.products
    FOR EACH ROW EXECUTE FUNCTION demo.audit_trigger_fn();

DROP TRIGGER IF EXISTS trg_audit_events ON demo.events;
CREATE TRIGGER trg_audit_events
    AFTER INSERT OR UPDATE OR DELETE ON demo.events
    FOR EACH ROW EXECUTE FUNCTION demo.audit_trigger_fn();

INSERT INTO demo.products (name, description, price, stock_quantity, category, tags, metadata)
SELECT * FROM (VALUES
    ('Wireless Headphones', 'Bluetooth 5.3 with ANC', 79.99, 150, 'Electronics',
     ARRAY['audio', 'bluetooth', 'featured'], '{"brand": "SoundMax", "color": "black"}'::jsonb),
    ('Mechanical Keyboard', 'Cherry MX Brown switches, RGB', 129.99, 75, 'Electronics',
     ARRAY['peripherals', 'gaming'], '{"brand": "KeyForge", "layout": "TKL"}'::jsonb),
    ('Python Cookbook', 'Advanced recipes for Python 3.12', 44.99, 200, 'Books',
     ARRAY['programming', 'bestseller'], '{"author": "A. Developer", "pages": 680}'::jsonb),
    ('USB-C Hub', '7-in-1 with HDMI and ethernet', 49.99, 300, 'Accessories',
     ARRAY['usb', 'hub', 'new'], '{"brand": "ConnectPro", "ports": 7}'::jsonb),
    ('Standing Desk Mat', 'Anti-fatigue ergonomic mat', 39.99, 90, 'Office',
     ARRAY['ergonomic', 'office'], '{"material": "polyurethane", "size": "20x36"}'::jsonb),
    ('4K Webcam', 'Ultra HD with autofocus and mic', 89.99, 60, 'Electronics',
     ARRAY['video', 'streaming'], '{"brand": "ClearView", "resolution": "4K"}'::jsonb),
    ('Laptop Stand', 'Adjustable aluminum stand', 34.99, 120, 'Accessories',
     ARRAY['ergonomic', 'laptop'], '{"material": "aluminum", "adjustable": true}'::jsonb),
    ('Data Engineering Book', 'Fundamentals of Data Engineering', 54.99, 85, 'Books',
     ARRAY['data', 'engineering', 'featured'], '{"author": "J. Reis", "pages": 450}'::jsonb)
) AS seed(name, description, price, stock_quantity, category, tags, metadata)
WHERE NOT EXISTS (SELECT 1 FROM demo.products LIMIT 1);
"""

with conn.cursor() as cur:
    cur.execute(SEED_SQL)
conn.commit()
print("✓ Demo schema created and seeded")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 5: Verify

# COMMAND ----------

from psycopg.rows import dict_row

cred = w.postgres.generate_database_credential(endpoint=endpoint.name)
params["password"] = cred.token

with psycopg.connect(**params, row_factory=dict_row) as verify_conn:
    with verify_conn.cursor() as cur:
        cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'demo' ORDER BY table_name")
        tables = [r["table_name"] for r in cur.fetchall()]
        print(f"Tables in demo schema: {tables}")

        cur.execute("SELECT count(*) as cnt FROM demo.products")
        cnt = cur.fetchone()["cnt"]
        print(f"Products seeded: {cnt}")

        cur.execute("SELECT version()")
        ver = cur.fetchone()["version"]
        print(f"PostgreSQL: {ver}")

conn.close()

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
print(f"  Schema:        demo")
print(f"  Username:      {user_email}")
print(f"  PG Version:    {PG_VERSION}")
print("=" * 60)
print()
print("Next steps — pick any lab path:")
print("  → labs/development-experience/  Branching, autoscaling, scale-to-zero")
print("  → labs/data-operations/         CRUD, JSONB, transactions, advanced SQL")
print("  → labs/reverse-etl/             Sync Delta Lake tables into Lakebase")
print("  → labs/observability/           pg_stat views, index analysis, monitoring")
print("  → labs/backup-recovery/         PITR, branch snapshots, instant restore")
print("  → labs/agentic-memory/          Persistent AI agent memory")
print("  → labs/authentication/          OAuth tokens, roles, permissions")
print("  → labs/app-deployment/          Full-stack Lab Console app (capstone)")
print()
print(f"  For app.yaml, set LAKEBASE_PROJECT_ID to: {PROJECT_ID}")

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
