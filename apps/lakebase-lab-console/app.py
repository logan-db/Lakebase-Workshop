"""
Lakebase Lab Console -- FastAPI application entry point.

Serves the React frontend as static files and exposes API routes
for branch management, compute, load testing, CRUD, and agent memory.
"""

import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.routes_branches import router as branches_router
from backend.routes_compute import router as compute_router
from backend.routes_loadtest import router as loadtest_router
from backend.routes_data import router as data_router
from backend.routes_agent import router as agent_router
from backend.routes_observability import router as observability_router
from backend.routes_online_tables import router as online_tables_router

app = FastAPI(
    title="Lakebase Lab Console",
    description="Interactive workshop app for exploring Databricks Lakebase Autoscaling",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(branches_router)
app.include_router(compute_router)
app.include_router(loadtest_router)
app.include_router(data_router)
app.include_router(agent_router)
app.include_router(observability_router)
app.include_router(online_tables_router)

STATIC_DIR = Path(__file__).parent / "frontend" / "dist"


@app.get("/api/health")
def health():
    project_id = os.getenv("LAKEBASE_PROJECT_ID", "NOT SET")
    pghost = os.getenv("PGHOST", "NOT SET")
    return {
        "status": "ok",
        "project_id": project_id,
        "pghost": pghost,
        "frontend_built": STATIC_DIR.exists(),
    }


@app.get("/api/config")
def get_config():
    host = os.getenv("DATABRICKS_HOST", "")
    if host and not host.startswith("https://"):
        host = f"https://{host}"
    return {
        "project_id": os.getenv("LAKEBASE_PROJECT_ID", ""),
        "branch_id": os.getenv("LAKEBASE_BRANCH_ID", "production"),
        "database": os.getenv("PGDATABASE", "databricks_postgres"),
        "schema": os.getenv("LAKEBASE_SCHEMA", "public"),
        "pghost_set": bool(os.getenv("PGHOST")),
        "workspace_host": host,
    }


@app.get("/api/dbtest")
def db_test():
    try:
        from backend.db import execute_query
        result = execute_query("SELECT version() as version, current_database() as db")
        return {"db_connected": True, "info": result[0]}
    except Exception as e:
        return {"db_connected": False, "error": str(e)}


# Serve the pre-built React SPA from frontend/dist/.
# The frontend must be built before deployment (npm run build).
if STATIC_DIR.exists():
    assets_dir = STATIC_DIR / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        file_path = STATIC_DIR / full_path
        if full_path and file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(STATIC_DIR / "index.html")
