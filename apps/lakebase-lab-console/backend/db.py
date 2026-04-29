"""
Lakebase connection manager with automatic OAuth token refresh.

Supports two modes:
  1. Databricks App runtime: uses auto-injected PG* env vars + SDK credential generation
  2. Direct SDK mode: discovers endpoint host from project ID

The project ID is resolved automatically:
  - From LAKEBASE_PROJECT_ID env var if set
  - Otherwise, auto-discovered by matching PGHOST against accessible Lakebase projects

Provides both single connections and a connection pool for high-throughput workloads.
"""

import asyncio
import logging
import os
import time
import threading
from contextlib import contextmanager

import psycopg
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

logger = logging.getLogger(__name__)

_workspace_client = None
_current_token: str | None = None
_last_refresh: float = 0
_TOKEN_REFRESH_INTERVAL = 2700  # 45 minutes (tokens expire at 60 min)

_connection_pools: dict[str, ConnectionPool] = {}
_pool_lock = threading.Lock()

_resolved_project_id: str | None = None


def _get_workspace_client():
    global _workspace_client
    if _workspace_client is None:
        from databricks.sdk import WorkspaceClient
        _workspace_client = WorkspaceClient()
    return _workspace_client


def get_project_id() -> str:
    """Resolve the Lakebase project ID (cached after first call).

    Resolution order:
      1. LAKEBASE_PROJECT_ID env var (explicit config)
      2. Auto-discover by matching PGHOST against accessible project endpoints
    """
    global _resolved_project_id
    if _resolved_project_id:
        return _resolved_project_id

    pid = os.getenv("LAKEBASE_PROJECT_ID", "").strip()
    if pid:
        _resolved_project_id = pid
        logger.info("Project ID from env: %s", pid)
        return pid

    pghost = os.getenv("PGHOST", "")
    if pghost:
        try:
            w = _get_workspace_client()
            for project in w.postgres.list_projects():
                proj_name = project.name or ""
                proj_id = proj_name.split("/")[-1] if "/" in proj_name else proj_name
                try:
                    endpoints = list(w.postgres.list_endpoints(
                        parent=f"projects/{proj_id}/branches/production"
                    ))
                    for ep in endpoints:
                        detail = w.postgres.get_endpoint(name=ep.name)
                        if (detail.status and detail.status.hosts
                                and detail.status.hosts.host == pghost):
                            _resolved_project_id = proj_id
                            logger.info("Auto-discovered project ID from PGHOST: %s", proj_id)
                            return proj_id
                except Exception:
                    continue
        except Exception as e:
            logger.warning("Project auto-discovery failed: %s", e)

    raise RuntimeError(
        "Cannot determine LAKEBASE_PROJECT_ID. "
        "Set it in app.yaml or attach a Lakebase database resource to the app."
    )


def get_schema() -> str:
    """Resolve the Lakebase schema name.

    Resolution order:
      1. LAKEBASE_SCHEMA env var (explicit config)
      2. Derived from project ID: lakebase-lab-foo → lakebase_lab_foo
    """
    explicit = os.getenv("LAKEBASE_SCHEMA", "").strip()
    if explicit:
        return explicit
    return get_project_id().replace("-", "_")


def _refresh_token() -> str:
    """Generate a fresh database credential token."""
    global _current_token, _last_refresh

    now = time.time()
    if _current_token and (now - _last_refresh) < _TOKEN_REFRESH_INTERVAL:
        return _current_token

    w = _get_workspace_client()
    branch_id = os.getenv("LAKEBASE_BRANCH_ID", "production")

    try:
        project_id = get_project_id()
        endpoints = list(
            w.postgres.list_endpoints(
                parent=f"projects/{project_id}/branches/{branch_id}"
            )
        )
        endpoint_name = endpoints[0].name if endpoints else None
        cred = w.postgres.generate_database_credential(endpoint=endpoint_name)
        _current_token = cred.token
    except RuntimeError:
        _current_token = w.config.oauth_token().access_token

    _last_refresh = now
    return _current_token


def _build_conninfo(branch_id: str | None = None) -> str:
    """Build a libpq connection string."""
    pghost = os.getenv("PGHOST")
    pguser = os.getenv("PGUSER")
    pgdatabase = os.getenv("PGDATABASE", "databricks_postgres")
    schema = get_schema()

    if not branch_id:
        branch_id = os.getenv("LAKEBASE_BRANCH_ID", "production")

    if pghost and pguser:
        token = _refresh_token()
        return (
            f"host={pghost} dbname={pgdatabase} user={pguser} "
            f"password={token} sslmode=require "
            f"options=-c\\ search_path={schema},public"
        )

    project_id = get_project_id()
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
    return (
        f"host={host} dbname={pgdatabase} user={username} "
        f"password={cred.token} sslmode=require "
        f"options=-c\\ search_path={schema},public"
    )


def _get_connection_params(branch_id: str | None = None) -> dict:
    """Build psycopg connection parameters."""
    pghost = os.getenv("PGHOST")
    pguser = os.getenv("PGUSER")
    pgdatabase = os.getenv("PGDATABASE", "databricks_postgres")

    if not branch_id:
        branch_id = os.getenv("LAKEBASE_BRANCH_ID", "production")

    schema = get_schema()
    search_path_opt = f"-c search_path={schema},public"

    if pghost and pguser:
        token = _refresh_token()
        return {
            "host": pghost,
            "dbname": pgdatabase,
            "user": pguser,
            "password": token,
            "sslmode": "require",
            "options": search_path_opt,
        }

    project_id = get_project_id()
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

    return {
        "host": host,
        "dbname": pgdatabase,
        "user": username,
        "password": cred.token,
        "sslmode": "require",
        "options": search_path_opt,
    }


def get_pool(branch_id: str | None = None, min_size: int = 4, max_size: int = 20) -> ConnectionPool:
    """Get or create a connection pool for the given branch."""
    key = branch_id or os.getenv("LAKEBASE_BRANCH_ID", "production")
    if key in _connection_pools:
        pool = _connection_pools[key]
        if not pool.closed:
            return pool

    with _pool_lock:
        if key in _connection_pools and not _connection_pools[key].closed:
            return _connection_pools[key]

        conninfo = _build_conninfo(branch_id)
        pool = ConnectionPool(
            conninfo=conninfo,
            min_size=min_size,
            max_size=max_size,
            kwargs={"row_factory": dict_row},
            open=True,
        )
        _connection_pools[key] = pool
        return pool


def close_all_pools():
    """Close all connection pools (call on shutdown)."""
    for pool in _connection_pools.values():
        try:
            pool.close()
        except Exception:
            pass
    _connection_pools.clear()


@contextmanager
def get_connection(branch_id: str | None = None):
    """Context manager that yields a psycopg connection with dict_row."""
    params = _get_connection_params(branch_id)
    conn = psycopg.connect(**params, row_factory=dict_row)
    try:
        yield conn
    finally:
        conn.close()


@contextmanager
def get_pooled_connection(branch_id: str | None = None):
    """Context manager that yields a connection from the pool."""
    pool = get_pool(branch_id)
    with pool.connection() as conn:
        conn.row_factory = dict_row
        yield conn


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


def get_db_metrics(branch_id: str | None = None) -> dict:
    """Fetch real-time DB-level metrics from pg_stat views."""
    try:
        with get_pooled_connection(branch_id) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT
                        numbackends AS active_connections,
                        xact_commit + xact_rollback AS total_transactions,
                        xact_commit AS commits,
                        tup_returned AS rows_read,
                        tup_inserted AS rows_inserted,
                        tup_updated AS rows_updated,
                        tup_deleted AS rows_deleted,
                        blks_hit AS cache_hits,
                        blks_read AS disk_reads
                    FROM pg_stat_database
                    WHERE datname = current_database()
                """)
                row = cur.fetchone()
                if row:
                    hits = row.get("cache_hits", 0) or 0
                    reads = row.get("disk_reads", 0) or 0
                    total = hits + reads
                    row["cache_hit_ratio"] = round(hits / total * 100, 1) if total > 0 else 100.0
                return row or {}
    except Exception:
        return {}
