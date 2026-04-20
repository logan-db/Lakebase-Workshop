# Databricks notebook source
# MAGIC %md
# MAGIC # Lab Setup (shared)
# MAGIC This notebook is `%run` by each lab to provide common utilities.
# MAGIC **Do not run this notebook directly.**

# COMMAND ----------

import re
import psycopg
from psycopg.rows import dict_row
from databricks.sdk import WorkspaceClient

w = WorkspaceClient()
user_email = w.current_user.me().user_name

def _sanitize(email):
    name = email.split("@")[0]
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9-]", "-", name.lower())).strip("-")

PROJECT_ID = f"lakebase-lab-{_sanitize(user_email)}"

def get_connection(branch="production"):
    """Connect to a Lakebase branch. Returns a psycopg connection with dict_row."""
    endpoints = list(w.postgres.list_endpoints(
        parent=f"projects/{PROJECT_ID}/branches/{branch}"
    ))
    ep = w.postgres.get_endpoint(name=endpoints[0].name)
    host = ep.status.hosts.host
    cred = w.postgres.generate_database_credential(endpoint=endpoints[0].name)
    params = {"host": host, "dbname": "databricks_postgres",
              "user": user_email, "password": cred.token, "sslmode": "require"}
    return psycopg.connect(**params, row_factory=dict_row)

def get_endpoint_name(branch="production"):
    """Get the full endpoint resource name for a branch."""
    return f"projects/{PROJECT_ID}/branches/{branch}/endpoints/primary"

print(f"Project: {PROJECT_ID}")
print(f"User:    {user_email}")
