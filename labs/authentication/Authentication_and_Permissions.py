# Databricks notebook source
# MAGIC %md
# MAGIC # Authentication & Permissions
# MAGIC
# MAGIC **Path:** Authentication &nbsp;|&nbsp; **Prerequisite:** `00_Setup_Lakebase_Project`
# MAGIC
# MAGIC **Lakebase features:** OAuth token auth, two-layer permission model, role grants
# MAGIC
# MAGIC In this notebook you will:
# MAGIC 1. Understand the two-layer permission model (workspace vs. database)
# MAGIC 2. Generate and inspect an OAuth database credential
# MAGIC 3. Explore token lifecycle (1-hour expiry, refresh patterns)
# MAGIC 4. Grant permissions to other users and Service Principals
# MAGIC 5. Learn how to connect with external tools (psql, DBeaver)
# MAGIC
# MAGIC **Run `00_Setup_Lakebase_Project` first.**

# COMMAND ----------

# MAGIC %pip install "databricks-sdk>=0.81.0" "psycopg[binary]>=3.0" --quiet

# COMMAND ----------

dbutils.library.restartPython()

# COMMAND ----------

# MAGIC %run ../_setup

# COMMAND ----------

import json, base64

ENDPOINT_NAME = get_endpoint_name()
show_app_link("auth", "Auth & Permissions")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Two-Layer Permission Model
# MAGIC
# MAGIC Lakebase has **two independent permission layers**:
# MAGIC
# MAGIC | Layer | What It Controls | Managed Via |
# MAGIC |-------|-----------------|-------------|
# MAGIC | **Workspace (Control Plane)** | Who can create/delete projects, branches, resize compute | Databricks workspace IAM |
# MAGIC | **Database (Data Plane)** | Who can read/write PostgreSQL tables, schemas, sequences | SQL `GRANT` statements |
# MAGIC
# MAGIC A user can have workspace permissions to manage branches but no access
# MAGIC to the data inside them — and vice versa. Both layers must be configured
# MAGIC for full access.
# MAGIC
# MAGIC **Docs:** [Roles and permissions](https://docs.databricks.com/aws/en/oltp/projects/roles-permissions)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. OAuth Database Credentials
# MAGIC
# MAGIC Lakebase uses **OAuth tokens** (not static passwords) for database
# MAGIC authentication. Tokens are generated via the Databricks SDK and have
# MAGIC a **1-hour TTL**. Open connections remain active even after token expiry —
# MAGIC expiration is only enforced at login.
# MAGIC
# MAGIC **Docs:** [Authentication](https://docs.databricks.com/aws/en/oltp/projects/authentication)

# COMMAND ----------

cred = w.postgres.generate_database_credential(endpoint=ENDPOINT_NAME)

print(f"Token preview:  {cred.token[:40]}...")
print(f"Expires at:     {cred.expire_time}")
print(f"Token length:   {len(cred.token)} characters")

# COMMAND ----------

# MAGIC %md
# MAGIC ### Inspecting the Token (JWT)
# MAGIC
# MAGIC The credential is a standard JWT. Let's decode the payload to see
# MAGIC what's inside — without verifying the signature.

# COMMAND ----------

parts = cred.token.split(".")
if len(parts) >= 2:
    payload = parts[1]
    payload += "=" * (4 - len(payload) % 4)  # pad base64
    decoded = json.loads(base64.urlsafe_b64decode(payload))
    print("JWT payload:")
    for k, v in decoded.items():
        print(f"  {k}: {v}")

# COMMAND ----------

# MAGIC %md
# MAGIC ### Key Observations
# MAGIC
# MAGIC - `sub` = your Databricks identity (email)
# MAGIC - `exp` = expiration timestamp (~1 hour from `iat`)
# MAGIC - `iss` = your workspace's OIDC endpoint
# MAGIC - The token is **not a static password** — it rotates automatically
# MAGIC
# MAGIC ### Token Rotation in Production
# MAGIC
# MAGIC OAuth tokens expire after one hour. Applications that maintain long-running
# MAGIC database connections must implement token rotation. There are two recommended
# MAGIC approaches:
# MAGIC
# MAGIC **Option 1: psycopg3 Connection Pool** — generates a fresh token for each
# MAGIC new connection from the pool:
# MAGIC
# MAGIC ```python
# MAGIC from databricks.sdk import WorkspaceClient
# MAGIC import psycopg
# MAGIC from psycopg_pool import ConnectionPool
# MAGIC
# MAGIC w = WorkspaceClient()
# MAGIC
# MAGIC class CustomConnection(psycopg.Connection):
# MAGIC     @classmethod
# MAGIC     def connect(cls, conninfo='', **kwargs):
# MAGIC         endpoint = "projects/<project-id>/branches/<branch-id>/endpoints/<endpoint-id>"
# MAGIC         credential = w.postgres.generate_database_credential(endpoint=endpoint)
# MAGIC         kwargs['password'] = credential.token
# MAGIC         return super().connect(conninfo, **kwargs)
# MAGIC
# MAGIC pool = ConnectionPool(
# MAGIC     conninfo=f"dbname=databricks_postgres user={username} host={host} sslmode=require",
# MAGIC     connection_class=CustomConnection,
# MAGIC     min_size=1,
# MAGIC     max_size=10,
# MAGIC     open=True,
# MAGIC )
# MAGIC ```
# MAGIC
# MAGIC **Option 2: SQLAlchemy** — uses an event listener to refresh the token
# MAGIC before it expires (2-minute buffer):
# MAGIC
# MAGIC ```python
# MAGIC from databricks.sdk import WorkspaceClient
# MAGIC from sqlalchemy import create_engine, event
# MAGIC import time
# MAGIC
# MAGIC w = WorkspaceClient()
# MAGIC endpoint = "projects/<project-id>/branches/<branch-id>/endpoints/<endpoint-id>"
# MAGIC engine = create_engine(f"postgresql+psycopg://{username}:@{host}:5432/databricks_postgres?sslmode=require")
# MAGIC
# MAGIC postgres_password = None
# MAGIC token_expiry = 0.0
# MAGIC
# MAGIC @event.listens_for(engine, "do_connect")
# MAGIC def provide_token(dialect, conn_rec, cargs, cparams):
# MAGIC     global postgres_password, token_expiry
# MAGIC     if postgres_password is None or time.time() >= token_expiry - 120:
# MAGIC         credential = w.postgres.generate_database_credential(endpoint=endpoint)
# MAGIC         postgres_password = credential.token
# MAGIC         token_expiry = credential.expire_time.seconds
# MAGIC     cparams["password"] = postgres_password
# MAGIC ```
# MAGIC
# MAGIC **Docs:** [Token rotation examples](https://docs.databricks.com/aws/en/oltp/projects/authentication#token-rotation-examples)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Connect and Inspect Current Roles

# COMMAND ----------

ep = w.postgres.get_endpoint(name=ENDPOINT_NAME)
host = ep.status.hosts.host

params = {"host": host, "dbname": "databricks_postgres",
          "user": user_email, "password": cred.token, "sslmode": "require"}
conn = psycopg.connect(**params, row_factory=dict_row)
print("✓ Connected")

# COMMAND ----------

with conn.cursor() as cur:
    cur.execute("SELECT current_user, current_database(), inet_server_addr(), inet_server_port()")
    info = cur.fetchone()
    print(f"Current user:   {info['current_user']}")
    print(f"Database:       {info['current_database']}")
    print(f"Server:         {info['inet_server_addr']}:{info['inet_server_port']}")

# COMMAND ----------

# MAGIC %md
# MAGIC ### List All Roles
# MAGIC
# MAGIC Each Databricks user or Service Principal that connects gets a
# MAGIC PostgreSQL role matching their identity.

# COMMAND ----------

with conn.cursor() as cur:
    cur.execute("""
        SELECT rolname, rolsuper, rolcreaterole, rolcreatedb, rolcanlogin
        FROM pg_roles
        WHERE rolname NOT LIKE 'pg_%' AND rolname != 'rdsadmin'
        ORDER BY rolname
    """)
    print(f"{'Role':<50} {'Super':>5} {'Login':>5} {'CreateDB':>8}")
    print("-" * 75)
    for r in cur.fetchall():
        print(f"{r['rolname']:<50} {str(r['rolsuper']):>5} {str(r['rolcanlogin']):>5} {str(r['rolcreatedb']):>8}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Granting Permissions
# MAGIC
# MAGIC ### Grant Schema Access to Another User
# MAGIC
# MAGIC ```sql
# MAGIC -- Grant read access (replace <your_schema> with your Lakebase schema, e.g. PG_SCHEMA from notebook 00)
# MAGIC GRANT USAGE ON SCHEMA <your_schema> TO "colleague@company.com";
# MAGIC GRANT SELECT ON ALL TABLES IN SCHEMA <your_schema> TO "colleague@company.com";
# MAGIC
# MAGIC -- Grant read + write access
# MAGIC GRANT ALL ON SCHEMA <your_schema> TO "colleague@company.com";
# MAGIC GRANT ALL ON ALL TABLES IN SCHEMA <your_schema> TO "colleague@company.com";
# MAGIC GRANT USAGE ON ALL SEQUENCES IN SCHEMA <your_schema> TO "colleague@company.com";
# MAGIC ```
# MAGIC
# MAGIC ### Grant Access to a Service Principal (for Apps)
# MAGIC
# MAGIC When deploying a Databricks App, the app runs as a Service Principal.
# MAGIC You must grant the SP access to your data.
# MAGIC
# MAGIC **Docs:** [Manage roles](https://docs.databricks.com/aws/en/oltp/projects/manage-roles) |
# MAGIC [Connect a Databricks App to Lakebase](https://docs.databricks.com/aws/en/oltp/projects/tutorial-databricks-apps-autoscaling)
# MAGIC
# MAGIC ```sql
# MAGIC GRANT ALL ON SCHEMA <your_schema> TO "<SP_CLIENT_ID>";
# MAGIC GRANT ALL ON ALL TABLES IN SCHEMA <your_schema> TO "<SP_CLIENT_ID>";
# MAGIC GRANT ALL ON ALL SEQUENCES IN SCHEMA <your_schema> TO "<SP_CLIENT_ID>";
# MAGIC
# MAGIC -- For future tables (so new tables are automatically accessible)
# MAGIC ALTER DEFAULT PRIVILEGES IN SCHEMA <your_schema>
# MAGIC     GRANT ALL ON TABLES TO "<SP_CLIENT_ID>";
# MAGIC ALTER DEFAULT PRIVILEGES IN SCHEMA <your_schema>
# MAGIC     GRANT USAGE ON SEQUENCES TO "<SP_CLIENT_ID>";
# MAGIC ```

# COMMAND ----------

# MAGIC %md
# MAGIC ### Check Existing Grants on Your Schema

# COMMAND ----------

with conn.cursor() as cur:
    cur.execute(f"""
        SELECT grantee, privilege_type, table_name
        FROM information_schema.table_privileges
        WHERE table_schema = '{PG_SCHEMA}'
        ORDER BY table_name, grantee, privilege_type
    """)
    rows = cur.fetchall()
    if rows:
        print(f"{'Table':<25} {'Grantee':<40} {'Privilege':<15}")
        print("-" * 80)
        for r in rows:
            print(f"{r['table_name']:<25} {r['grantee']:<40} {r['privilege_type']:<15}")
    else:
        print("No explicit grants found (you're the owner, so you have implicit access)")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5. Connecting with External Tools
# MAGIC
# MAGIC You can connect to Lakebase from any PostgreSQL client. The key
# MAGIC requirement: you must use an OAuth token as the password.
# MAGIC
# MAGIC ### psql (Command Line)
# MAGIC
# MAGIC ```bash
# MAGIC # Generate a token
# MAGIC TOKEN=$(databricks postgres generate-database-credential \
# MAGIC   "projects/<project-id>/branches/production/endpoints/primary" \
# MAGIC   --profile <profile> -o json | python3 -c "import sys,json; print(json.load(sys.stdin)['token'])")
# MAGIC
# MAGIC # Connect
# MAGIC PGPASSWORD="$TOKEN" psql \
# MAGIC   -h <endpoint-host> \
# MAGIC   -U <your-email> \
# MAGIC   -d databricks_postgres \
# MAGIC   --set=sslmode=require
# MAGIC ```
# MAGIC
# MAGIC ### DBeaver / DataGrip / pgAdmin
# MAGIC
# MAGIC | Setting | Value |
# MAGIC |---------|-------|
# MAGIC | Host | *(endpoint host from notebook 00)* |
# MAGIC | Port | 5432 |
# MAGIC | Database | `databricks_postgres` |
# MAGIC | Username | *(your Databricks email)* |
# MAGIC | Password | *(OAuth token — regenerate every hour)* |
# MAGIC | SSL Mode | `require` |
# MAGIC
# MAGIC > **Tip:** Some tools support "password command" to auto-refresh.
# MAGIC > Set it to the `databricks postgres generate-database-credential` command above.

# COMMAND ----------

print("Your connection details:")
print(f"  Host:     {host}")
print(f"  Port:     5432")
print(f"  Database: databricks_postgres")
print(f"  Username: {user_email}")
print(f"  SSL:      require")
print(f"\n  Generate a token with:")
print(f'  databricks postgres generate-database-credential "{ENDPOINT_NAME}" --profile <your-profile> -o json')

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
# MAGIC | **Backup & Recovery** | `labs/backup-recovery/` | Point-in-time recovery, branch snapshots, instant restore |
# MAGIC | **Agentic Memory** | `labs/agentic-memory/` | Persistent AI agent memory with session/message storage |
# MAGIC | **Online Feature Store** | `labs/online-feature-store/` | Real-time ML feature serving powered by Lakebase Autoscaling |
# MAGIC | **App Deployment** | `labs/app-deployment/` | Full-stack React + FastAPI app using Lakebase (capstone) |
