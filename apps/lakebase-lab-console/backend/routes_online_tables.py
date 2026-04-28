"""Online Tables / Feature Store routes via Databricks SDK."""

import os
from fastapi import APIRouter, HTTPException
from databricks.sdk import WorkspaceClient

router = APIRouter(prefix="/api/online-tables", tags=["online-tables"])


def _get_project_id() -> str:
    pid = os.getenv("LAKEBASE_PROJECT_ID")
    if not pid:
        raise HTTPException(500, "LAKEBASE_PROJECT_ID not configured")
    return pid


@router.get("/stores")
def list_online_stores():
    """List all online stores (Lakebase-backed feature serving endpoints)."""
    try:
        w = WorkspaceClient()
        project_id = _get_project_id()
        stores = list(w.postgres.list_online_stores(
            parent=f"projects/{project_id}"
        ))
        result = []
        for store in stores:
            info = {
                "name": store.name,
                "store_id": store.name.split("/")[-1] if store.name else "",
            }
            if hasattr(store, "status") and store.status:
                s = store.status
                info["state"] = str(getattr(s, "current_state", "")) if s else None
                info["detailed_state"] = str(getattr(s, "detailed_state", "")) if s else None
            if hasattr(store, "spec") and store.spec:
                spec = store.spec
                info["source_table"] = getattr(spec, "source_table_full_name", None)
                info["primary_key_columns"] = list(getattr(spec, "primary_key_columns", []) or [])
            result.append(info)
        return result
    except HTTPException:
        raise
    except Exception as e:
        if "not found" in str(e).lower() or "UNIMPLEMENTED" in str(e) or "does not have" in str(e).lower():
            return []
        raise HTTPException(500, f"Failed to list online stores: {e}")


@router.get("/synced-tables")
def list_synced_tables():
    """List synced database tables (reverse ETL)."""
    try:
        w = WorkspaceClient()
        project_id = _get_project_id()

        branches = list(w.postgres.list_branches(parent=f"projects/{project_id}"))
        all_synced = []

        for branch in branches:
            branch_id = branch.name.split("/")[-1] if branch.name else ""
            try:
                synced = list(w.database.list_synced_database_tables(
                    parent=f"projects/{project_id}/branches/{branch_id}"
                ))
                for table in synced:
                    info = {
                        "name": table.name,
                        "branch_id": branch_id,
                        "table_id": table.name.split("/")[-1] if table.name else "",
                    }
                    if hasattr(table, "status") and table.status:
                        info["state"] = str(getattr(table.status, "current_state", ""))
                        info["pipeline_id"] = getattr(table.status, "pipeline_id", None)
                    if hasattr(table, "spec") and table.spec:
                        info["source_table"] = getattr(table.spec, "source_table_full_name", None)
                        info["primary_key_columns"] = list(
                            getattr(table.spec, "primary_key_columns", []) or []
                        )
                        policy = getattr(table.spec, "scheduling_policy", None)
                        info["scheduling_policy"] = str(policy) if policy else None
                    all_synced.append(info)
            except Exception:
                continue

        return all_synced
    except HTTPException:
        raise
    except Exception as e:
        if "not found" in str(e).lower() or "UNIMPLEMENTED" in str(e):
            return []
        raise HTTPException(500, f"Failed to list synced tables: {e}")


@router.post("/synced-tables/{table_id}/trigger")
def trigger_synced_table(table_id: str, pipeline_id: str | None = None):
    """Trigger a sync pipeline update for a synced table."""
    try:
        w = WorkspaceClient()
        if not pipeline_id:
            raise HTTPException(400, "pipeline_id is required to trigger a sync")
        w.pipelines.start_update(pipeline_id=pipeline_id)
        return {"message": f"Sync pipeline {pipeline_id} triggered for {table_id}"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Failed to trigger sync: {e}")


@router.get("/feature-specs")
def list_feature_specs():
    """List Unity Catalog online table specs (feature serving) if available."""
    try:
        w = WorkspaceClient()
        tables = list(w.online_tables.list())
        result = []
        for t in tables:
            info = {
                "name": t.name,
            }
            if hasattr(t, "status") and t.status:
                info["state"] = str(getattr(t.status, "detailed_state", ""))
                info["triggered_update_status"] = str(
                    getattr(t.status, "triggered_update_status", "")
                )
            if hasattr(t, "spec") and t.spec:
                info["source_table"] = getattr(t.spec, "source_table_full_name", None)
                info["primary_key_columns"] = list(
                    getattr(t.spec, "primary_key_columns", []) or []
                )
                info["run_triggered"] = getattr(t.spec, "run_triggered", None)
                info["run_continuously"] = getattr(t.spec, "run_continuously", None)
            result.append(info)
        return result
    except Exception as e:
        if "not found" in str(e).lower() or "UNIMPLEMENTED" in str(e):
            return []
        raise HTTPException(500, f"Failed to list feature specs: {e}")
