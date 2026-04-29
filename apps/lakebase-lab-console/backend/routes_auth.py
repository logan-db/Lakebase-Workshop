"""Authentication & Permissions routes."""

import base64
import json
import os

from fastapi import APIRouter, HTTPException

from .db import get_project_id, get_schema

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.get("/credential")
def generate_credential():
    """Generate an OAuth database credential and decode its JWT payload."""
    try:
        from databricks.sdk import WorkspaceClient

        w = WorkspaceClient()
        project_id = get_project_id()
        branch_id = os.getenv("LAKEBASE_BRANCH_ID", "production")

        endpoints = list(
            w.postgres.list_endpoints(
                parent=f"projects/{project_id}/branches/{branch_id}"
            )
        )
        if not endpoints:
            raise HTTPException(404, "No endpoints found")

        cred = w.postgres.generate_database_credential(endpoint=endpoints[0].name)

        jwt_claims = {}
        parts = cred.token.split(".")
        if len(parts) >= 2:
            payload = parts[1]
            payload += "=" * (4 - len(payload) % 4)
            try:
                jwt_claims = json.loads(base64.urlsafe_b64decode(payload))
            except Exception:
                pass

        return {
            "token_preview": cred.token[:40] + "...",
            "token_length": len(cred.token),
            "expire_time": str(cred.expire_time),
            "jwt_claims": jwt_claims,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Failed to generate credential: {e}")


@router.get("/roles")
def list_roles():
    """List PostgreSQL roles (filtered)."""
    try:
        from backend.db import execute_query

        rows = execute_query("""
            SELECT rolname, rolsuper, rolcreaterole, rolcreatedb, rolcanlogin
            FROM pg_roles
            WHERE rolname NOT LIKE 'pg_%%' AND rolname != 'rdsadmin'
            ORDER BY rolname
        """)
        return rows
    except Exception as e:
        raise HTTPException(500, f"Failed to list roles: {e}")


@router.get("/grants")
def list_grants():
    """List table grants for the configured schema."""
    try:
        from backend.db import execute_query

        schema = get_schema()
        rows = execute_query(
            """
            SELECT grantee, privilege_type, table_name
            FROM information_schema.table_privileges
            WHERE table_schema = %s
            ORDER BY table_name, grantee, privilege_type
            """,
            (schema,),
        )
        return rows
    except Exception as e:
        raise HTTPException(500, f"Failed to list grants: {e}")


@router.get("/connection-info")
def connection_info():
    """Return connection details for external tools."""
    try:
        from databricks.sdk import WorkspaceClient

        try:
            project_id = get_project_id()
        except RuntimeError:
            project_id = ""
        branch_id = os.getenv("LAKEBASE_BRANCH_ID", "production")
        pghost = os.getenv("PGHOST", "")

        host = pghost
        username = os.getenv("PGUSER", "")

        if not host and project_id:
            w = WorkspaceClient()
            endpoints = list(
                w.postgres.list_endpoints(
                    parent=f"projects/{project_id}/branches/{branch_id}"
                )
            )
            if endpoints:
                ep = w.postgres.get_endpoint(name=endpoints[0].name)
                host = ep.status.hosts.host
            username = username or w.current_user.me().user_name

        return {
            "host": host or "N/A",
            "port": 5432,
            "database": os.getenv("PGDATABASE", "databricks_postgres"),
            "username": username or "N/A",
            "ssl_mode": "require",
            "project_id": project_id,
            "branch_id": branch_id,
        }
    except Exception as e:
        raise HTTPException(500, f"Failed to get connection info: {e}")
