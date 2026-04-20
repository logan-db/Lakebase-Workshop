# Permissions Guide

## Two Permission Layers

Lakebase has two independent permission layers:

1. **Workspace permissions** -- who can manage the Lakebase project (create/delete branches, resize compute)
2. **Database permissions** -- who can read/write PostgreSQL tables

## Databricks Apps: Service Principal Grants

When you deploy a Databricks App and add a Lakebase database as a resource, the App runs as a **Service Principal (SP)**. You must create an OAuth-enabled Postgres role for the SP and grant it access to your schemas and tables.

See the [official tutorial](https://docs.databricks.com/aws/en/oltp/projects/tutorial-databricks-apps-autoscaling) for the full walkthrough.

### Finding the Service Principal ID

**From a notebook or script** (recommended):

```python
app = w.apps.get(name="lakebase-lab-console")
sp = w.service_principals.get(id=app.service_principal_id)
print(sp.application_id)  # This is the SP client ID
```

**From the UI:** Go to **Compute → Apps → your-app → Environment tab** and find the `DATABRICKS_CLIENT_ID` value.

### Step 1: Create the OAuth Role

The `databricks_auth` extension enables OAuth authentication so the SP can connect using Databricks-managed tokens. Connect to your Lakebase database as the project owner (your user) and run:

```sql
-- Enable the Databricks authentication extension
CREATE EXTENSION IF NOT EXISTS databricks_auth;

-- Create an OAuth-enabled Postgres role for the SP
-- Replace <SP_CLIENT_ID> with the actual DATABRICKS_CLIENT_ID
SELECT databricks_create_role('<SP_CLIENT_ID>', 'service_principal');
```

### Step 2: Grant Schema Access

```sql
-- Replace <SP_CLIENT_ID> with the actual Service Principal client ID

-- Grant schema access
GRANT ALL ON SCHEMA demo TO "<SP_CLIENT_ID>";

-- Grant access to all current tables and sequences
GRANT ALL ON ALL TABLES IN SCHEMA demo TO "<SP_CLIENT_ID>";
GRANT ALL ON ALL SEQUENCES IN SCHEMA demo TO "<SP_CLIENT_ID>";

-- Grant access to future tables (recommended)
ALTER DEFAULT PRIVILEGES IN SCHEMA demo
    GRANT ALL ON TABLES TO "<SP_CLIENT_ID>";
ALTER DEFAULT PRIVILEGES IN SCHEMA demo
    GRANT ALL ON SEQUENCES TO "<SP_CLIENT_ID>";
```

> **Important:** You must use `databricks_create_role()` to create the SP's Postgres role.
> Without it, the role will show "No login" in the Lakebase Roles UI, causing "password
> authentication failed" errors even though the grants are correct.

### Where to Run SQL Against Lakebase

You can run these commands from:

1. **Lakebase SQL Editor** — open the SQL editor in the Databricks UI for your Lakebase instance
2. **A Databricks notebook** — use psycopg3 + SDK credentials (if connected to the instance)
3. **psql** on your local machine using the endpoint host
4. **DBeaver** or any PostgreSQL client

Example using a notebook with `get_connection()`:

```python
# Use the get_connection() function from any workshop notebook
conn = get_connection()
with conn.cursor() as cur:
    cur.execute("CREATE EXTENSION IF NOT EXISTS databricks_auth")
    cur.execute("SELECT databricks_create_role('<SP_CLIENT_ID>', 'service_principal')")
    cur.execute('GRANT ALL ON SCHEMA demo TO "<SP_CLIENT_ID>"')
    cur.execute('GRANT ALL ON ALL TABLES IN SCHEMA demo TO "<SP_CLIENT_ID>"')
    cur.execute('GRANT ALL ON ALL SEQUENCES IN SCHEMA demo TO "<SP_CLIENT_ID>"')
    cur.execute('ALTER DEFAULT PRIVILEGES IN SCHEMA demo GRANT ALL ON TABLES TO "<SP_CLIENT_ID>"')
conn.commit()
```

## Synced Table Permissions (Important)

Synced tables (Reverse ETL) are created by the Lakebase sync pipeline, which uses a different internal role. This means:

- `ALTER DEFAULT PRIVILEGES` from your user **does not** cover synced tables
- After a sync completes, you must **re-grant** access to the SP:

```sql
GRANT ALL ON ALL TABLES IN SCHEMA demo TO "<SP_CLIENT_ID>";
```

## Control Plane Permissions (Branch/Endpoint Management)

For the Lab Console to manage branches and endpoints via the `w.postgres` SDK, the App's Service Principal needs **Lakebase project-level permissions** in the workspace.

If the SP does not have these permissions, the Branch Manager and Autoscaling tabs will show errors. In this case:

- A facilitator can manage branches from the CLI or a notebook
- The app will still work for data operations (CRUD, load test, agent memory)

### Degraded Mode

The Lab Console detects permission errors and shows helpful messages directing users to CLI/notebook alternatives when the SP lacks control plane access.
