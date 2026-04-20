# Permissions Guide

## Two Permission Layers

Lakebase has two independent permission layers:

1. **Workspace permissions** -- who can manage the Lakebase project (create/delete branches, resize compute)
2. **Database permissions** -- who can read/write PostgreSQL tables

## Databricks Apps: Service Principal Grants

When you deploy a Databricks App and add a Lakebase database as a resource, the App runs as a **Service Principal (SP)**. The SP gets a PostgreSQL role automatically, but you must grant it access to your schemas and tables.

### Finding the Service Principal ID

Option A: Check the app logs for "OAuth token identity" errors -- it shows the SP ID.

Option B: Go to **Admin Console > Service Principals** in your workspace.

### Granting Schema Access

Connect to your Lakebase database as the project owner (your user) and run:

```sql
-- Replace <SP_CLIENT_ID> with the actual Service Principal client ID

-- Grant schema access
GRANT USAGE ON SCHEMA demo TO "<SP_CLIENT_ID>";

-- Grant read access to all current tables
GRANT SELECT ON ALL TABLES IN SCHEMA demo TO "<SP_CLIENT_ID>";

-- Grant write access (INSERT, UPDATE, DELETE)
GRANT INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA demo TO "<SP_CLIENT_ID>";

-- Grant access to future tables (recommended)
ALTER DEFAULT PRIVILEGES IN SCHEMA demo
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO "<SP_CLIENT_ID>";

-- Grant sequence usage (needed for SERIAL/auto-increment columns)
GRANT USAGE ON ALL SEQUENCES IN SCHEMA demo TO "<SP_CLIENT_ID>";
ALTER DEFAULT PRIVILEGES IN SCHEMA demo
    GRANT USAGE ON SEQUENCES TO "<SP_CLIENT_ID>";
```

### Running SQL Against Lakebase

You can run these grants from:

1. **A Databricks notebook** using psycopg3 + SDK credentials
2. **psql** on your local machine using the endpoint host from the bootstrap output
3. **DBeaver** or any PostgreSQL client

Example using the Authentication lab (`labs/authentication/`) or any psycopg connection:

```python
# Use the get_connection() function from any workshop notebook
with conn.cursor() as cur:
    cur.execute('GRANT USAGE ON SCHEMA demo TO "<SP_CLIENT_ID>"')
    cur.execute('GRANT ALL ON ALL TABLES IN SCHEMA demo TO "<SP_CLIENT_ID>"')
    cur.execute('GRANT USAGE ON ALL SEQUENCES IN SCHEMA demo TO "<SP_CLIENT_ID>"')
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
