"""
Lakebase connection manager with automatic OAuth token refresh.

Supports two modes:
  1. Databricks App runtime: uses auto-injected PG* env vars + SDK credential generation
  2. Direct SDK mode: discovers endpoint host from project ID
"""

import asyncio
import os
import subprocess
import socket
import time
from contextlib import contextmanager

import psycopg
from psycopg.rows import dict_row


_workspace_client = None
_current_token: str | None = None
_last_refresh: float = 0
_TOKEN_REFRESH_INTERVAL = 2700  # 45 minutes (tokens expire at 60 min)


def _get_workspace_client():
    global _workspace_client
    if _workspace_client is None:
        from databricks.sdk import WorkspaceClient
        _workspace_client = WorkspaceClient()
    return _workspace_client


def _resolve_hostname(hostname: str) -> str | None:
    """Resolve hostname, falling back to dig on macOS."""
    try:
        return socket.gethostbyname(hostname)
    except socket.gaierror:
        pass
    try:
        result = subprocess.run(
            ["dig", "+short", hostname],
            capture_output=True, text=True, timeout=5,
        )
        for line in result.stdout.strip().split("\n"):
            line = line.strip()
            if line and not line.startswith(";"):
                return line
    except Exception:
        pass
    return None


def _refresh_token() -> str:
    """Generate a fresh database credential token."""
    global _current_token, _last_refresh

    now = time.time()
    if _current_token and (now - _last_refresh) < _TOKEN_REFRESH_INTERVAL:
        return _current_token

    w = _get_workspace_client()
    project_id = os.getenv("LAKEBASE_PROJECT_ID", "")
    branch_id = os.getenv("LAKEBASE_BRANCH_ID", "production")

    if project_id:
        endpoints = list(
            w.postgres.list_endpoints(
                parent=f"projects/{project_id}/branches/{branch_id}"
            )
        )
        endpoint_name = endpoints[0].name if endpoints else None
        cred = w.postgres.generate_database_credential(endpoint=endpoint_name)
        _current_token = cred.token
    else:
        _current_token = w.config.oauth_token().access_token

    _last_refresh = now
    return _current_token


def _get_connection_params(branch_id: str | None = None) -> dict:
    """Build psycopg connection parameters."""
    pghost = os.getenv("PGHOST")
    pguser = os.getenv("PGUSER")
    pgdatabase = os.getenv("PGDATABASE", "databricks_postgres")
    project_id = os.getenv("LAKEBASE_PROJECT_ID", "")

    if not branch_id:
        branch_id = os.getenv("LAKEBASE_BRANCH_ID", "production")

    if pghost and pguser:
        token = _refresh_token()
        params = {
            "host": pghost,
            "dbname": pgdatabase,
            "user": pguser,
            "password": token,
            "sslmode": "require",
        }
    elif project_id:
        w = _get_workspace_client()
        endpoints = list(
            w.postgres.list_endpoints(
                parent=f"projects/{project_id}/branches/{branch_id}"
            )
        )
        if not endpoints:
            raise RuntimeError(f"No endpoints for {project_id}/{branch_id}")

        ep = w.postgres.get_endpoint(name=endpoints[0].name)
        host = ep.status.hosts.host
        cred = w.postgres.generate_database_credential(endpoint=endpoints[0].name)
        username = w.current_user.me().user_name

        params = {
            "host": host,
            "dbname": pgdatabase,
            "user": username,
            "password": cred.token,
            "sslmode": "require",
        }
    else:
        raise RuntimeError(
            "Set PGHOST/PGUSER or LAKEBASE_PROJECT_ID to connect to Lakebase"
        )

    hostaddr = _resolve_hostname(params["host"])
    if hostaddr:
        params["hostaddr"] = hostaddr

    return params


@contextmanager
def get_connection(branch_id: str | None = None):
    """Context manager that yields a psycopg connection with dict_row."""
    params = _get_connection_params(branch_id)
    conn = psycopg.connect(**params, row_factory=dict_row)
    try:
        yield conn
    finally:
        conn.close()


def execute_query(sql: str, params: tuple | None = None, branch_id: str | None = None) -> list[dict]:
    """Execute a query and return results as list of dicts."""
    with get_connection(branch_id) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            if cur.description:
                return cur.fetchall()
            conn.commit()
            return [{"rowcount": cur.rowcount}]


def execute_write(sql: str, params: tuple | None = None, branch_id: str | None = None) -> list[dict]:
    """Execute a write query (INSERT/UPDATE/DELETE), commit, return results."""
    with get_connection(branch_id) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            if cur.description:
                result = cur.fetchall()
                conn.commit()
                return result
            conn.commit()
            return [{"rowcount": cur.rowcount}]
